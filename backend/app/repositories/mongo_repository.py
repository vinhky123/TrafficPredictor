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

    def get_latest_speed(self, location_collection: str) -> float | None:
        db = self.client[self.db_name]
        collection = db[location_collection]
        result = collection.find_one({}, {"Speed": 1, "_id": 0}, sort=[("_id", -1)])
        if not result:
            return None
        return result.get("Speed")

    def get_recent_speeds(self, location_collection: str, limit: int = 96) -> list[float]:
        db = self.client[self.db_name]
        collection = db[location_collection]
        results = collection.find({}, {"Speed": 1, "_id": 0}).sort("_id", -1).limit(limit)
        return [record.get("Speed") for record in results if record.get("Speed") is not None]

    def get_latest_prediction(self, name: str) -> list[float] | None:
        db = self.client[self.db_name]
        collection = db["Predictions"]
        result = collection.find_one({"Name": name}, {"Speed": 1, "_id": 0}, sort=[("_id", -1)])
        if not result:
            return None
        speeds = result.get("Speed")
        return speeds if isinstance(speeds, list) else None

    def insert_prediction(self, time: str, name: str, speeds: list[float]) -> None:
        db = self.client[self.db_name]
        collection = db["Predictions"]
        collection.insert_one({"Time": time, "Name": name, "Speed": speeds})

