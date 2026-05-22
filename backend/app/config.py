from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    mongo_uri: str | None = None
    mongo_db_name: str = "Traffic"
    mongo_pool_size: int = 100

    model_path: str = os.path.join(os.path.dirname(__file__), "notebook", "TimeXer.pth")

    segments_table: str = "traffic-predictor-dev-road-segments"
    speeds_table: str = "traffic-predictor-dev-speeds"
    predictions_table: str = "traffic-predictor-dev-predictions"
    connections_table: str = "traffic-predictor-dev-connections"
    aws_region: str = "ap-southeast-1"

    @staticmethod
    def from_env() -> "Settings":
        mongo_uri = os.getenv("MONGODB_URI") or os.getenv("URI") or os.getenv("uri")
        mongo_db_name = os.getenv("MONGODB_DB_NAME", "Traffic")
        mongo_pool_size = int(os.getenv("MONGODB_POOL_SIZE", "100"))

        model_path = os.getenv("MODEL_PATH") or os.path.join(
            os.path.dirname(__file__), "notebook", "TimeXer.pth"
        )

        segments_table = os.getenv("SEGMENTS_TABLE", "traffic-predictor-dev-road-segments")
        speeds_table = os.getenv("SPEEDS_TABLE", "traffic-predictor-dev-speeds")
        predictions_table = os.getenv("PREDICTIONS_TABLE", "traffic-predictor-dev-predictions")
        connections_table = os.getenv("CONNECTIONS_TABLE", "traffic-predictor-dev-connections")
        aws_region = os.getenv("AWS_REGION", "ap-southeast-1")

        return Settings(
            mongo_uri=mongo_uri,
            mongo_db_name=mongo_db_name,
            mongo_pool_size=mongo_pool_size,
            model_path=model_path,
            segments_table=segments_table,
            speeds_table=speeds_table,
            predictions_table=predictions_table,
            connections_table=connections_table,
            aws_region=aws_region,
        )

