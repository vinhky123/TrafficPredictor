import hashlib
import json
import logging
import os
from datetime import datetime

import boto3

logger = logging.getLogger(__name__)


def _normalize_shape(links: list[dict]) -> list[dict]:
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


def handler(event, context):
    segments_table_name = os.environ["SEGMENTS_TABLE"]
    raw_bucket = event.get("raw_bucket") or os.environ.get("RAW_BUCKET")
    raw_key = event.get("raw_key")
    processed_bucket = os.environ.get("PROCESSED_BUCKET", raw_bucket)

    ddb = boto3.resource("dynamodb")
    table = ddb.Table(segments_table_name)
    s3 = boto3.client("s3")

    obj = s3.get_object(Bucket=raw_bucket, Key=raw_key)
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

    lines = []
    for rec in records:
        rec["speed_kmh"] = round(float(rec["speed_ms"]) * 3.6, 2)
        rec["ingested_at"] = datetime.utcnow().isoformat()
        lines.append(json.dumps(rec))

    body = "\n".join(lines)

    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    output_key = f"transformed/traffic/{ts}.jsonl"

    s3.put_object(Bucket=processed_bucket, Key=output_key, Body=body.encode(), ContentType="application/jsonl")

    logger.info("Wrote %d transformed records → s3://%s/%s", len(lines), processed_bucket, output_key)

    return {"bucket": processed_bucket, "key": output_key, "count": len(lines)}
