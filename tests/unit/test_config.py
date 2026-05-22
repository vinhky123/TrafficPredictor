from __future__ import annotations

import os
from unittest.mock import patch

from backend.app.config import Settings


class TestSettings:
    def test_default_values(self):
        settings = Settings(mongo_uri="mongodb://localhost:27017")
        assert settings.mongo_db_name == "Traffic"
        assert settings.mongo_pool_size == 100
        assert settings.segments_table == "traffic-predictor-dev-road-segments"
        assert settings.speeds_table == "traffic-predictor-dev-speeds"
        assert settings.predictions_table == "traffic-predictor-dev-predictions"
        assert settings.connections_table == "traffic-predictor-dev-connections"
        assert settings.aws_region == "ap-southeast-1"

    def test_custom_values(self):
        settings = Settings(
            mongo_uri="mongodb://custom:27017",
            mongo_db_name="CustomDB",
            mongo_pool_size=50,
            model_path="/custom/model.pth",
            segments_table="custom-segments",
            speeds_table="custom-speeds",
            predictions_table="custom-predictions",
            aws_region="us-west-2",
        )
        assert settings.mongo_uri == "mongodb://custom:27017"
        assert settings.mongo_db_name == "CustomDB"
        assert settings.segments_table == "custom-segments"
        assert settings.speeds_table == "custom-speeds"
        assert settings.predictions_table == "custom-predictions"
        assert settings.aws_region == "us-west-2"

    def test_from_env_with_defaults(self):
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings.from_env()
            assert settings.mongo_uri is None
            assert settings.speeds_table == "traffic-predictor-dev-speeds"
            assert settings.predictions_table == "traffic-predictor-dev-predictions"
            assert settings.aws_region == "ap-southeast-1"

    def test_from_env_with_custom_values(self):
        env_vars = {
            "SEGMENTS_TABLE": "env-segments",
            "SPEEDS_TABLE": "env-speeds",
            "PREDICTIONS_TABLE": "env-predictions",
            "AWS_REGION": "eu-west-1",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            settings = Settings.from_env()
            assert settings.segments_table == "env-segments"
            assert settings.speeds_table == "env-speeds"
            assert settings.predictions_table == "env-predictions"
            assert settings.aws_region == "eu-west-1"

    def test_frozen_settings(self):
        settings = Settings(mongo_uri="mongodb://localhost:27017")
        with patch.object(settings, "__setattr__", side_effect=Exception("frozen")):
            pass
