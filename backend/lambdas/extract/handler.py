import json
import logging
import os
from datetime import datetime

import boto3
import requests

logger = logging.getLogger(__name__)


def handler(event, context):
    api_key = os.environ["HERE_API_KEY"]
    raw_bucket = os.environ["RAW_BUCKET"]
    center_lat = os.environ.get("CENTER_LAT", "10.776889")
    center_lng = os.environ.get("CENTER_LNG", "106.695278")
    radius_m = os.environ.get("RADIUS_M", "15000")

    params = {
        "apiKey": api_key,
        "in": f"circle:{center_lat},{center_lng};r={radius_m}",
        "locationReferencing": "shape",
    }

    logger.info("Extracting from HERE API — centre=(%s, %s) radius=%sm", center_lat, center_lng, radius_m)

    resp = requests.get(
        "https://data.traffic.hereapi.com/v7/flow",
        params=params,
        timeout=30,
    )
    resp.raise_for_status()
    payload = resp.json()

    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    key = f"raw/traffic/{ts}.json"

    s3 = boto3.client("s3")
    s3.put_object(Bucket=raw_bucket, Key=key, Body=json.dumps(payload).encode(), ContentType="application/json")

    logger.info("Uploaded raw snapshot → s3://%s/%s", raw_bucket, key)

    return {"status": "ok", "bucket": raw_bucket, "key": key, "results_count": len(payload.get("results", []))}
