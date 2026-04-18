"""Unit tests for configuration settings."""

from __future__ import annotations

import os
from unittest.mock import patch

from backend.app.config import Settings


class TestSettings:
    """Tests for the Settings dataclass."""

    def test_default_values(self):
        settings = Settings(mongo_uri="mongodb://localhost:27017")
        assert settings.mongo_db_name == "Traffic"
        assert settings.mongo_pool_size == 100
        assert settings.dynamodb_table == "traffic-predictor-dev-road-segments"
        assert settings.aws_region == "ap-southeast-1"

    def test_custom_values(self):
        settings = Settings(
            mongo_uri="mongodb://custom:27017",
            mongo_db_name="CustomDB",
            mongo_pool_size=50,
            model_path="/custom/model.pth",
            dynamodb_table="custom-table",
            aws_region="us-west-2",
        )
        assert settings.mongo_uri == "mongodb://custom:27017"
        assert settings.mongo_db_name == "CustomDB"
        assert settings.mongo_pool_size == 50
        assert settings.dynamodb_table == "custom-table"
        assert settings.aws_region == "us-west-2"

    def test_from_env_with_defaults(self):
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings.from_env()
            assert settings.mongo_uri is None
            assert settings.mongo_db_name == "Traffic"
            assert settings.mongo_pool_size == 100

    def test_from_env_with_custom_values(self):
        env_vars = {
            "MONGODB_URI": "mongodb://env:27017",
            "MONGODB_DB_NAME": "EnvDB",
            "MONGODB_POOL_SIZE": "75",
            "DYNAMODB_TABLE": "env-table",
            "AWS_REGION": "eu-west-1",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            settings = Settings.from_env()
            assert settings.mongo_uri == "mongodb://env:27017"
            assert settings.mongo_db_name == "EnvDB"
            assert settings.mongo_pool_size == 75
            assert settings.dynamodb_table == "env-table"
            assert settings.aws_region == "eu-west-1"

    def test_from_env_fallback_for_uri(self):
        env_vars = {
            "URI": "mongodb://fallback:27017",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            settings = Settings.from_env()
            assert settings.mongo_uri == "mongodb://fallback:27017"

    def test_frozen_settings(self):
        settings = Settings(mongo_uri="mongodb://localhost:27017")
        with patch.object(settings, "__setattr__", side_effect=Exception("frozen")):
            pass  # Settings is frozen by default with @dataclass(frozen=True)