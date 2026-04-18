"""Pytest configuration and fixtures for the TrafficPredictor test suite."""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask

from backend.app import create_app
from backend.app.config import Settings


class MockMongoClient:
    """Mock MongoDB client for testing."""

    def __init__(self, *args, **kwargs):
        self._databases: dict = {}

    def __getitem__(self, name: str):
        if name not in self._databases:
            self._databases[name] = MockDatabase()
        return self._databases[name]

    def close(self):
        pass


class MockDatabase:
    """Mock MongoDB database."""

    def __init__(self):
        self._collections: dict = {}

    def __getitem__(self, name: str):
        if name not in self._collections:
            self._collections[name] = MockCollection()
        return self._collections[name]


class MockCollection:
    """Mock MongoDB collection."""

    def __init__(self):
        self._documents: list = []

    def find_one(self, *args, **kwargs):
        if self._documents:
            return self._documents[-1]
        return None

    def find(self, *args, **kwargs):
        return MockCursor(self._documents)

    def insert_one(self, document: dict):
        self._documents.append(document)

    def insert_many(self, documents: list):
        self._documents.extend(documents)

    def create_index(self, *args, **kwargs):
        pass


class MockCursor:
    """Mock MongoDB cursor."""

    def __init__(self, documents: list):
        self._documents = documents
        self._sort_field = None
        self._sort_order = None
        self._limit_value = None

    def sort(self, *args, **kwargs):
        self._sort_field = args[0] if args else kwargs.get("key_or_list")
        self._sort_order = args[1] if len(args) > 1 else kwargs.get("direction", -1)
        return self

    def limit(self, value: int):
        self._limit_value = value
        return self

    def __iter__(self):
        results = self._documents
        if self._limit_value:
            results = results[: self._limit_value]
        return iter(results)


@pytest.fixture
def test_settings() -> Settings:
    """Create test settings with mock values."""
    return Settings(
        mongo_uri="mongodb://localhost:27017",
        mongo_db_name="TrafficTest",
        mongo_pool_size=10,
        model_path="/tmp/fake_model.pth",
        dynamodb_table="test-road-segments",
        aws_region="us-east-1",
    )


@pytest.fixture
def app(test_settings: Settings) -> Flask:
    """Create a Flask application for testing."""
    with patch("backend.app.MongoRepository") as mock_repo:
        mock_repo.from_uri.return_value = MagicMock()
        with patch("backend.app.TimeXerModel") as mock_model:
            mock_model.from_path.return_value = MagicMock()
            with patch("backend.app.SegmentMapping") as mock_mapper:
                mock_mapper.return_value = MagicMock()
                app = create_app(test_settings)
                app.config["TESTING"] = True
                yield app


@pytest.fixture
def client(app: Flask):
    """Create a test client for the Flask application."""
    return app.test_client()


@pytest.fixture
def mock_mongo_client():
    """Create a mock MongoDB client."""
    return MockMongoClient()