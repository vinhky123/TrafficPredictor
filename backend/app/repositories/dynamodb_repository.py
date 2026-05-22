"""DynamoDB repository for traffic data storage and retrieval."""

from __future__ import annotations

import json
from dataclasses import dataclass

import boto3
from boto3.dynamodb.conditions import Key


@dataclass
class DynamoDBRepository:
    segments_table: str
    speeds_table: str
    predictions_table: str
    region: str = "ap-southeast-1"

    def _get_table(self, table_name: str):
        ddb = boto3.resource("dynamodb", region_name=self.region)
        return ddb.Table(table_name)

    def get_latest_speed(self, segment_index: int) -> float | None:
        table = self._get_table(self.speeds_table)
        resp = table.query(
            KeyConditionExpression=Key("segment_index").eq(segment_index),
            ScanIndexForward=False,
            Limit=1,
        )
        items = resp.get("Items", [])
        if not items:
            return None
        return items[0].get("speed_kmh")

    def get_recent_speeds(self, segment_index: int, limit: int = 96) -> list[float]:
        table = self._get_table(self.speeds_table)
        resp = table.query(
            KeyConditionExpression=Key("segment_index").eq(segment_index),
            ScanIndexForward=False,
            Limit=limit,
        )
        return [item["speed_kmh"] for item in resp.get("Items", []) if item.get("speed_kmh") is not None]

    def get_latest_prediction(self, segment_index: int) -> list[float] | None:
        table = self._get_table(self.predictions_table)
        resp = table.query(
            KeyConditionExpression=Key("segment_index").eq(segment_index),
            ScanIndexForward=False,
            Limit=1,
        )
        items = resp.get("Items", [])
        if not items:
            return None
        speeds = items[0].get("speeds")
        if isinstance(speeds, str):
            speeds = json.loads(speeds)
        return speeds if isinstance(speeds, list) else None

    def insert_prediction(self, time: str, segment_index: int, speeds: list[float]) -> None:
        table = self._get_table(self.predictions_table)
        table.put_item(Item={
            "segment_index": segment_index,
            "timestamp": time,
            "speeds": speeds,
        })

    def insert_speed_records(self, records: list[dict]) -> None:
        if not records:
            return
        table = self._get_table(self.speeds_table)
        with table.batch_writer() as batch:
            for record in records:
                batch.put_item(Item=record)

    def get_segments(self, segment_mapping) -> list[dict]:
        return segment_mapping.get_all_segments()
