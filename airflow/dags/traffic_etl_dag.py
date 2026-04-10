"""Traffic ETL + Prediction DAG.

Pipeline stages (matching the architecture diagram):
    1. **Extract**  — Pull real-time traffic flow from the HERE API.
    2. **Upload**   — Persist the raw JSON snapshot to S3.
    3. **Transform** — Read raw data, apply PySpark transformations
                       (filter roads, compute speed/jam metrics), write
                       cleaned Parquet back to S3.
    4. **Load**     — Upsert transformed records into DocumentDB (MongoDB).
    5. **Predict**  — Notify the Flask backend to run TimeXer inference.

Runs every 5 minutes.  All external credentials are pulled from Airflow
Variables so the DAG file itself contains no secrets.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta

import boto3
import pendulum
import requests
from airflow import DAG
from airflow.models import Variable
from airflow.operators.python import PythonOperator
from pymongo import MongoClient

logger = logging.getLogger(__name__)

# ── Airflow Variables (set via UI or terraform) ──────────────────────────
_var = Variable.get  # shorthand


def _s3_client():
    return boto3.client("s3", region_name=_var("AWS_REGION", default_var="ap-southeast-1"))


# ── 1. Extract ───────────────────────────────────────────────────────────

def extract_traffic_data(**context) -> str:
    """Fetch traffic flow data from the HERE Traffic Flow API."""
    api_key = _var("HERE_API_KEY", default_var="demo-key")
    center_lat = float(_var("HERE_CENTER_LAT", default_var="10.777195"))
    center_lng = float(_var("HERE_CENTER_LNG", default_var="106.695364"))
    radius_m = int(_var("HERE_RADIUS_M", default_var="20000"))

    params = {
        "apiKey": api_key,
        "in": f"circle:{center_lat},{center_lng};r={radius_m}",
        "locationReferencing": "shape",
    }

    logger.info("Extracting from HERE API — centre=(%s, %s) radius=%sm",
                center_lat, center_lng, radius_m)

    resp = requests.get(
        "https://data.traffic.hereapi.com/v7/flow",
        params=params,
        timeout=30,
    )
    resp.raise_for_status()

    payload = resp.json()
    logger.info("Extracted %d flow results", len(payload.get("results", [])))
    return json.dumps(payload)


# ── 2. Upload raw JSON to S3 ─────────────────────────────────────────────

def upload_raw_to_s3(ti, **context) -> str:
    """Persist the raw HERE response as a timestamped JSON file on S3."""
    raw_json: str = ti.xcom_pull(task_ids="extract")
    bucket = _var("S3_BUCKET", default_var="traffic-predictor-data")
    ts = context["ts_nodash"]
    key = f"raw/traffic/{ts}.json"

    s3 = _s3_client()
    s3.put_object(Bucket=bucket, Key=key, Body=raw_json.encode(), ContentType="application/json")
    logger.info("Uploaded raw snapshot → s3://%s/%s", bucket, key)

    return json.dumps({"bucket": bucket, "key": key})


# ── 3. Transform with PySpark ────────────────────────────────────────────

def transform_traffic_data(ti, **context) -> str:
    """Read raw JSON from S3, apply PySpark transformations, write Parquet.

    Transformations:
    - Parse ``results[].currentFlow`` into flat records.
    - Filter to monitored road segments (by index mapping).
    - Compute ``speed_kmh`` from ``speed`` (m/s → km/h).
    - Add ingestion timestamp.
    """
    from pyspark.sql import SparkSession
    from pyspark.sql import functions as F

    meta = json.loads(ti.xcom_pull(task_ids="upload_raw"))
    bucket = meta["bucket"]
    raw_key = meta["key"]

    spark = SparkSession.builder.appName("traffic_transform").getOrCreate()

    try:
        s3 = _s3_client()
        obj = s3.get_object(Bucket=bucket, Key=raw_key)
        raw = json.loads(obj["Body"].read().decode())

        records = []
        for result in raw.get("results", []):
            flow = result.get("currentFlow", {})
            location = result.get("location", {})
            records.append({
                "speed_ms": flow.get("speed", 0),
                "jam_factor": flow.get("jamFactor", 0),
                "free_flow_speed": flow.get("freeFlow", 0),
                "confidence": flow.get("confidence", 0),
                "shape": json.dumps(location.get("shape", {}).get("links", [])),
            })

        df = spark.createDataFrame(records)
        df = (
            df
            .withColumn("speed_kmh", F.round(F.col("speed_ms") * 3.6, 2))
            .withColumn("ingested_at", F.lit(datetime.utcnow().isoformat()))
        )

        ts = context["ts_nodash"]
        output_key = f"transformed/traffic/{ts}"
        output_path = f"s3a://{bucket}/{output_key}"

        df.write.mode("overwrite").parquet(output_path)
        logger.info("Wrote %d transformed records → %s", df.count(), output_path)

        return json.dumps({"bucket": bucket, "key": output_key, "count": df.count()})
    finally:
        spark.stop()


# ── 4. Load into DocumentDB / MongoDB ────────────────────────────────────

def load_to_documentdb(ti, **context) -> str:
    """Upsert transformed speed records into MongoDB/DocumentDB collections.

    Each monitored location has its own collection.  Records are inserted
    with the latest speed reading so the backend can query the most recent
    N entries for prediction input.
    """
    from pyspark.sql import SparkSession

    meta = json.loads(ti.xcom_pull(task_ids="transform"))
    bucket = meta["bucket"]
    parquet_key = meta["key"]

    mongo_uri = _var("MONGODB_URI", default_var="mongodb://localhost:27017")
    db_name = _var("MONGODB_DB_NAME", default_var="Traffic")

    spark = SparkSession.builder.appName("traffic_load").getOrCreate()

    try:
        df = spark.read.parquet(f"s3a://{bucket}/{parquet_key}")
        records = [row.asDict() for row in df.collect()]

        client = MongoClient(mongo_uri)
        db = client[db_name]

        inserted = 0
        for record in records:
            speed_collection = db["SpeedRecords"]
            speed_collection.insert_one({
                "Speed": record["speed_ms"],
                "SpeedKmh": record["speed_kmh"],
                "JamFactor": record["jam_factor"],
                "FreeFlow": record["free_flow_speed"],
                "Confidence": record["confidence"],
                "IngestedAt": record["ingested_at"],
            })
            inserted += 1

        client.close()
        logger.info("Loaded %d records into DocumentDB (%s)", inserted, db_name)

        return json.dumps({"inserted": inserted})
    finally:
        spark.stop()


# ── 5. Trigger prediction via Backend API ────────────────────────────────

def trigger_prediction(**context) -> None:
    """POST to the backend ``/api/db_notice`` endpoint to run model inference.

    The backend will fetch the latest 96 time-steps per location from MongoDB,
    run the TimeXer model, and write predictions back to the ``Predictions``
    collection.
    """
    backend_url = _var("BACKEND_URL", default_var="http://backend:5000")
    url = f"{backend_url}/api/db_notice"

    resp = requests.post(url, json={"notice": "update"}, timeout=60)
    resp.raise_for_status()

    result = resp.json()
    logger.info("Prediction triggered — inserted %s forecasts", result.get("inserted"))


# ── DAG definition ───────────────────────────────────────────────────────

with DAG(
    dag_id="traffic_etl",
    description="Traffic ETL pipeline: HERE API → S3 → PySpark → DocumentDB → TimeXer prediction",
    start_date=pendulum.datetime(2024, 1, 1, tz="UTC"),
    schedule="*/5 * * * *",
    catchup=False,
    max_active_runs=1,
    default_args={
        "owner": "trafficpredictor",
        "retries": 2,
        "retry_delay": timedelta(minutes=2),
    },
    tags=["traffic", "etl", "here-api", "pyspark"],
) as dag:

    t_extract = PythonOperator(
        task_id="extract",
        python_callable=extract_traffic_data,
    )

    t_upload = PythonOperator(
        task_id="upload_raw",
        python_callable=upload_raw_to_s3,
    )

    t_transform = PythonOperator(
        task_id="transform",
        python_callable=transform_traffic_data,
    )

    t_load = PythonOperator(
        task_id="load",
        python_callable=load_to_documentdb,
    )

    t_predict = PythonOperator(
        task_id="predict",
        python_callable=trigger_prediction,
    )

    t_extract >> t_upload >> t_transform >> t_load >> t_predict
