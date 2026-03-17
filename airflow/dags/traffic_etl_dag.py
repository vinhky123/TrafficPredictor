from __future__ import annotations

import json
import logging
from datetime import timedelta

import pendulum
from airflow import DAG
from airflow.models import Variable
from airflow.operators.python import PythonOperator


logger = logging.getLogger(__name__)


def extract_traffic_data(**_context) -> str:
    """
    Extract traffic data from HERE Flow API.

    This is written as a portfolio-friendly task: it demonstrates how the
    orchestration would work on MWAA/Composer/Astronomer without requiring
    real credentials.
    """
    api_key = Variable.get("API_HERE_1", default_var="demo-key")
    radius_m = int(Variable.get("HERE_RADIUS_M", default_var="20000"))
    center_lat = float(Variable.get("HERE_CENTER_LAT", default_var="10.777195098260915"))
    center_lng = float(Variable.get("HERE_CENTER_LNG", default_var="106.69536391705417"))

    payload = {
        "source": "here_flow_api",
        "params": {
            "apiKey": api_key,
            "in": f"circle:{center_lat}, {center_lng};r={radius_m}",
            "locationReferencing": "shape",
        },
        "results": [],
    }

    logger.info("Extracted payload (demo) with %s", payload["params"])
    return json.dumps(payload)


def transform_traffic_data(ti, **_context) -> str:
    raw = ti.xcom_pull(task_ids="extract_traffic_data")
    data = json.loads(raw)

    # Demo transform: normalize into records of (index, speed, jamFactor).
    records = [
        {"index": 1, "speed": 12.3, "jamFactor": 7.1},
        {"index": 2, "speed": 23.4, "jamFactor": 4.2},
    ]
    out = {
        "meta": {"transformed_at": pendulum.now("UTC").to_iso8601_string()},
        "records": records,
    }
    logger.info("Transformed %s records (demo)", len(records))
    return json.dumps(out)


def load_to_storage(ti, **_context) -> str:
    transformed = ti.xcom_pull(task_ids="transform_traffic_data")
    _ = json.loads(transformed)

    # Demo load: show the intended destination.
    s3_bucket = Variable.get("S3_BUCKET", default_var="demo-bucket")
    prefix = Variable.get("S3_PREFIX_REALTIME", default_var="TrafficStreaming/real/")

    target = {"s3_bucket": s3_bucket, "prefix": prefix}
    logger.info("Loaded dataset to S3 (demo): %s", target)
    return json.dumps(target)


def run_prediction(ti, **_context) -> None:
    """
    Optional task. In the real system it would fetch the last N windows from S3,
    run a model inference, then write predictions back to S3 or MongoDB.
    """
    _target = ti.xcom_pull(task_ids="load_to_storage")
    model_name = Variable.get("MODEL_NAME", default_var="TimeXer")
    logger.info("Prediction completed (demo) using model=%s", model_name)


with DAG(
    dag_id="traffic_etl",
    description="Traffic ETL + prediction pipeline (portfolio demo)",
    start_date=pendulum.datetime(2024, 1, 1, tz="UTC"),
    schedule="*/5 * * * *",
    catchup=False,
    default_args={
        "owner": "trafficpredictor",
        "retries": 2,
        "retry_delay": timedelta(minutes=2),
    },
    tags=["traffic", "etl", "portfolio"],
) as dag:
    extract = PythonOperator(
        task_id="extract_traffic_data",
        python_callable=extract_traffic_data,
    )

    transform = PythonOperator(
        task_id="transform_traffic_data",
        python_callable=transform_traffic_data,
    )

    load = PythonOperator(
        task_id="load_to_storage",
        python_callable=load_to_storage,
    )

    predict = PythonOperator(
        task_id="run_prediction",
        python_callable=run_prediction,
    )

    extract >> transform >> load >> predict

