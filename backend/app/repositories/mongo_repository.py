from __future__ import annotations

from dataclasses import dataclass

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi


@dataclass(frozen=True)
class MongoRepository:
    client: MongoClient
    db_name: str

    @staticmethod
    def from_uri(uri: str, db_name: str, max_pool_size: int = 100) -> "MongoRepository":
        client = MongoClient(uri, server_api=ServerApi("1"), maxPoolSize=max_pool_size)
        return MongoRepository(client=client, db_name=db_name)

    def get_latest_speed(self, segment_index: int) -> float | None:
        db = self.client[self.db_name]
        result = db["SpeedRecords"].find_one(
            {"segment_index": segment_index},
            {"Speed": 1, "_id": 0},
            sort=[("_id", -1)],
        )
        if not result:
            return None
        return result.get("Speed")

    def get_recent_speeds(self, segment_index: int, limit: int = 96) -> list[float]:
        db = self.client[self.db_name]
        results = (
            db["SpeedRecords"]
            .find({"segment_index": segment_index}, {"Speed": 1, "_id": 0})
            .sort("_id", -1)
            .limit(limit)
        )
        return [r["Speed"] for r in results if r.get("Speed") is not None]

    def get_latest_prediction(self, segment_index: int) -> list[float] | None:
        db = self.client[self.db_name]
        result = db["Predictions"].find_one(
            {"segment_index": segment_index},
            {"Speed": 1, "_id": 0},
            sort=[("_id", -1)],
        )
        if not result:
            return None
        speeds = result.get("Speed")
        return speeds if isinstance(speeds, list) else None

    def insert_prediction(self, time: str, segment_index: int, speeds: list[float]) -> None:
        db = self.client[self.db_name]
        db["Predictions"].insert_one({
            "Time": time,
            "segment_index": segment_index,
            "Speed": speeds,
        })
