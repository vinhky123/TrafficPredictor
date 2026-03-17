from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    mongo_uri: str | None
    mongo_db_name: str = "Traffic"
    mongo_pool_size: int = 100

    model_path: str = os.path.join(os.path.dirname(__file__), "notebook", "TimeXer.pth")

    @staticmethod
    def from_env() -> "Settings":
        # Support both URI/uri because the legacy code uses "uri"
        mongo_uri = os.getenv("MONGODB_URI") or os.getenv("URI") or os.getenv("uri")
        mongo_db_name = os.getenv("MONGODB_DB_NAME", "Traffic")
        mongo_pool_size = int(os.getenv("MONGODB_POOL_SIZE", "100"))

        model_path = os.getenv("MODEL_PATH") or os.path.join(
            os.path.dirname(__file__), "notebook", "TimeXer.pth"
        )

        return Settings(
            mongo_uri=mongo_uri,
            mongo_db_name=mongo_db_name,
            mongo_pool_size=mongo_pool_size,
            model_path=model_path,
        )

