"""Traffic ETL + Prediction DAG.

Pipeline stages:
    1. **Extract**   — Pull real-time traffic flow from the HERE API
                       (15 km circle centred on Dinh Doc Lap).
    2. **Upload**    — Persist the raw JSON snapshot to S3.
    3. **Transform** — Parse road-segment shapes, register each segment in
                       DynamoDB (shape_hash → segment_index), compute speed
                       metrics, write cleaned Parquet back to S3.
    4. **Load**      — Insert transformed records into DocumentDB with
                       segment_index for per-segment time-series queries.
    5. **Predict**   — Notify the Flask backend to run batch TimeXer inference.

Runs every 5 minutes.  All external credentials are pulled from Airflow
Variables so the DAG file itself contains no secrets.

Telegram notifications are sent on DAG success, task failure, and retry.
"""

from __future__ import annotations

import hashlib
import json
import logging
import traceback
from datetime import datetime, timedelta

import boto3
import pendulum
import requests
from airflow import DAG
from airflow.models import Variable
from airflow.operators.python import PythonOperator
from pymongo import ASCENDING, MongoClient

logger = logging.getLogger(__name__)

_var = Variable.get


# ── Helpers ──────────────────────────────────────────────────────────────

def _s3_client():
    return boto3.client("s3", region_name=_var("AWS_REGION", default_var="ap-southeast-1"))


def _dynamodb_resource():
    return boto3.resource("dynamodb", region_name=_var("AWS_REGION", default_var="ap-southeast-1"))


def _normalize_shape(links: list[dict]) -> list[dict]:
    """Flatten shape links into a single ordered list of rounded points."""
    points: list[dict] = []
    for link in links:
        for pt in link.get("points", []):
            points.append({
                "lat": round(pt["lat"], 6),
                "lng": round(pt["lng"], 6),
            })
    return points


def _hash_shape(points: list[dict]) -> str:
    return hashlib.sha256(json.dumps(points).encode()).hexdigest()


def _get_or_create_segment(table, shape_hash: str, name: str, shape_json: str) -> int:
    """Lookup existing segment or register a new one with an atomic counter."""
    resp = table.get_item(Key={"shape_hash": shape_hash})
    item = resp.get("Item")
    if item:
        return int(item["segment_index"])

    counter_resp = table.update_item(
        Key={"shape_hash": "__COUNTER__"},
        UpdateExpression="ADD current_index :inc",
        ExpressionAttributeValues={":inc": 1},
        ReturnValues="UPDATED_NEW",
    )
    new_index = int(counter_resp["Attributes"]["current_index"])

    table.put_item(Item={
        "shape_hash": shape_hash,
        "segment_index": new_index,
        "name": name or f"segment_{new_index}",
        "shape": shape_json,
        "created_at": datetime.utcnow().isoformat(),
    })

    return new_index


# ── Telegram ─────────────────────────────────────────────────────────────

def _send_telegram(message: str) -> None:
    token = _var("TELEGRAM_BOT_TOKEN", default_var="")
    chat_id = _var("TELEGRAM_CHAT_ID", default_var="")
    if not token or not chat_id:
        logger.warning("Telegram credentials not configured — skipping notification")
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": message, "parse_mode": "HTML"},
            timeout=10,
        )
    except Exception:
        logger.exception("Failed to send Telegram notification")


def _on_success(context):
    dag_run = context["dag_run"]
    duration = dag_run.end_date - dag_run.start_date if dag_run.end_date else "n/a"
    _send_telegram(
        f"✅ <b>ETL SUCCESS</b>\n"
        f"Run: <code>{context['ts']}</code>\n"
        f"Duration: {duration}"
    )


def _on_failure(context):
    ti = context["task_instance"]
    _send_telegram(
        f"❌ <b>ETL FAILED</b>\n"
        f"Task: <code>{ti.task_id}</code>\n"
        f"Run: <code>{context['ts']}</code>\n"
        f"Error: <pre>{traceback.format_exc()[-500:]}</pre>"
    )


def _on_retry(context):
    ti = context["task_instance"]
    _send_telegram(
        f"🔄 <b>ETL RETRY</b>\n"
        f"Task: <code>{ti.task_id}</code> (attempt {ti.try_number})\n"
        f"Run: <code>{context['ts']}</code>"
    )


# ── 1. Extract ───────────────────────────────────────────────────────────

def extract_traffic_data(**context) -> str:
    """Fetch traffic flow data from the HERE Traffic Flow API.

    Centre: Dinh Doc Lap (Independence Palace), radius 15 km.
    """
    api_key = _var("HERE_API_KEY", default_var="demo-key")
    center_lat = float(_var("HERE_CENTER_LAT", default_var="10.776889"))
    center_lng = float(_var("HERE_CENTER_LNG", default_var="106.695278"))
    radius_m = int(_var("HERE_RADIUS_M", default_var="15000"))

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


# ── 3. Transform ─────────────────────────────────────────────────────────

def transform_traffic_data(ti, **context) -> str:
    """Parse road-segment shapes, register in DynamoDB, compute speed metrics."""
    from pyspark.sql import SparkSession
    from pyspark.sql import functions as F

    meta = json.loads(ti.xcom_pull(task_ids="upload_raw"))
    bucket, raw_key = meta["bucket"], meta["key"]

    table_name = _var("DYNAMODB_TABLE", default_var="traffic-predictor-dev-road-segments")
    ddb = _dynamodb_resource()
    table = ddb.Table(table_name)

    spark = SparkSession.builder.appName("traffic_transform").getOrCreate()

    try:
        s3 = _s3_client()
        obj = s3.get_object(Bucket=bucket, Key=raw_key)
        raw = json.loads(obj["Body"].read().decode())

        records = []
        for result in raw.get("results", []):
            flow = result.get("currentFlow", {})
            location = result.get("location", {})

            links = location.get("shape", {}).get("links", [])
            if not links:
                continue

            points = _normalize_shape(links)
            shape_hash = _hash_shape(points)
            segment_name = location.get("description", "")
            segment_index = _get_or_create_segment(
                table, shape_hash, segment_name, json.dumps(points),
            )

            records.append({
                "segment_index": segment_index,
                "shape_hash": shape_hash,
                "name": segment_name,
                "speed_ms": flow.get("speed", 0),
                "jam_factor": flow.get("jamFactor", 0),
                "free_flow_speed": flow.get("freeFlow", 0),
                "confidence": flow.get("confidence", 0),
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
        count = df.count()
        logger.info("Wrote %d transformed records → %s", count, output_path)

        return json.dumps({"bucket": bucket, "key": output_key, "count": count})
    finally:
        spark.stop()


# ── 4. Load into DocumentDB / MongoDB ────────────────────────────────────

def load_to_documentdb(ti, **context) -> str:
    """Insert speed records into a single SpeedRecords collection with segment_index."""
    from pyspark.sql import SparkSession

    meta = json.loads(ti.xcom_pull(task_ids="transform"))
    bucket, parquet_key = meta["bucket"], meta["key"]

    mongo_uri = _var("MONGODB_URI", default_var="mongodb://localhost:27017")
    db_name = _var("MONGODB_DB_NAME", default_var="Traffic")

    spark = SparkSession.builder.appName("traffic_load").getOrCreate()

    try:
        df = spark.read.parquet(f"s3a://{bucket}/{parquet_key}")
        records = [row.asDict() for row in df.collect()]

        client = MongoClient(mongo_uri)
        db = client[db_name]
        collection = db["SpeedRecords"]

        collection.create_index(
            [("segment_index", ASCENDING), ("_id", ASCENDING)],
            background=True,
        )

        docs = [
            {
                "segment_index": record["segment_index"],
                "Speed": record["speed_ms"],
                "SpeedKmh": record["speed_kmh"],
                "JamFactor": record["jam_factor"],
                "FreeFlow": record["free_flow_speed"],
                "Confidence": record["confidence"],
                "IngestedAt": record["ingested_at"],
            }
            for record in records
        ]

        if docs:
            collection.insert_many(docs)

        client.close()
        logger.info("Loaded %d records into DocumentDB (%s.SpeedRecords)", len(docs), db_name)

        return json.dumps({"inserted": len(docs)})
    finally:
        spark.stop()


# ── 5. Trigger prediction via Backend API ────────────────────────────────

def trigger_prediction(**context) -> None:
    """POST to the backend /api/db_notice endpoint to run batch model inference."""
    backend_url = _var("BACKEND_URL", default_var="http://backend:5000")
    url = f"{backend_url}/api/db_notice"

    resp = requests.post(url, json={"notice": "update"}, timeout=120)
    resp.raise_for_status()

    result = resp.json()
    logger.info("Prediction triggered — inserted %s forecasts", result.get("inserted"))


# ── DAG definition ───────────────────────────────────────────────────────

with DAG(
    dag_id="traffic_etl",
    description="Traffic ETL: HERE API → S3 → DynamoDB registry → DocumentDB → TimeXer batch prediction",
    start_date=pendulum.datetime(2024, 1, 1, tz="UTC"),
    schedule="*/5 * * * *",
    catchup=False,
    max_active_runs=1,
    on_success_callback=_on_success,
    default_args={
        "owner": "trafficpredictor",
        "retries": 2,
        "retry_delay": timedelta(minutes=2),
        "on_failure_callback": _on_failure,
        "on_retry_callback": _on_retry,
    },
    tags=["traffic", "etl", "here-api", "pyspark", "dynamodb"],
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
