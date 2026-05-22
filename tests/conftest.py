from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask

from backend.app import create_app
from backend.app.config import Settings


class MockDynamoDBTable:
    def __init__(self):
        self.items: list[dict] = []

    def query(self, **kwargs):
        return {"Items": []}

    def scan(self, **kwargs):
        return {"Items": []}

    def get_item(self, **kwargs):
        return {}

    def put_item(self, **kwargs):
        self.items.append(kwargs.get("Item", {}))

    def batch_writer(self):
        return self

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


class MockDynamoDBResource:
    def Table(self, name):
        return MockDynamoDBTable()


@pytest.fixture
def test_settings() -> Settings:
    return Settings(
        mongo_uri="mongodb://localhost:27017",
        mongo_db_name="TrafficTest",
        mongo_pool_size=10,
        model_path="/tmp/fake_model.pth",
        segments_table="test-segments",
        speeds_table="test-speeds",
        predictions_table="test-predictions",
        aws_region="us-east-1",
    )


@pytest.fixture
def app(test_settings: Settings) -> Flask:
    with patch("backend.app.repositories.dynamodb_repository.boto3.resource") as mock_resource:
        mock_resource.return_value = MockDynamoDBResource()
        with patch("backend.app.dependencies.boto3.resource") as mock_dep_resource:
            mock_dep_resource.return_value = MockDynamoDBResource()
            with patch("backend.app.TimeXerModel") as mock_model:
                mock_model.from_path.return_value = MagicMock()
                with patch("backend.app.SegmentMapping") as mock_mapper:
                    mock_mapper.return_value = MagicMock()
                    app = create_app(test_settings)
                    app.config["TESTING"] = True
                    yield app


@pytest.fixture
def client(app: Flask):
    return app.test_client()


@pytest.fixture
def mock_dynamodb():
    return MockDynamoDBResource()
