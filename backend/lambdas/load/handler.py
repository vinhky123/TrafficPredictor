import json
import logging
import os
from datetime import datetime

import boto3

logger = logging.getLogger(__name__)


def handler(event, context):
    speeds_table_name = os.environ["SPEEDS_TABLE"]
    processed_bucket = event.get("processed_bucket") or os.environ.get("PROCESSED_BUCKET")
    processed_key = event.get("processed_key")

    ddb = boto3.resource("dynamodb")
    table = ddb.Table(speeds_table_name)
    s3 = boto3.client("s3")

    obj = s3.get_object(Bucket=processed_bucket, Key=processed_key)
    body = obj["Body"].read().decode()

    records = []
    now = datetime.utcnow().isoformat()
    for line in body.strip().split("\n"):
        if not line.strip():
            continue
        rec = json.loads(line)
        records.append({
            "segment_index": rec["segment_index"],
            "timestamp": now,
            "speed_ms": rec["speed_ms"],
            "speed_kmh": rec["speed_kmh"],
            "jam_factor": rec.get("jam_factor", 0),
            "free_flow_speed": rec.get("free_flow_speed", 0),
            "confidence": rec.get("confidence", 0),
        })

    with table.batch_writer() as batch:
        for record in records:
            batch.put_item(Item=record)

    logger.info("Inserted %d speed records into DynamoDB", len(records))

    return {"inserted": len(records)}
