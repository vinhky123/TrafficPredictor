"""Integration tests for API endpoints."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask

from backend.app import create_app
from backend.app.config import Settings


class TestHealthEndpoint:
    """Tests for the health check endpoint."""

    @pytest.fixture
    def client(self):
        """Create a test client with mocked dependencies."""
        settings = Settings(
            mongo_uri="mongodb://localhost:27017",
            mongo_db_name="TrafficTest",
            mongo_pool_size=10,
            model_path="/tmp/fake_model.pth",
            dynamodb_table="test-road-segments",
            aws_region="us-east-1",
        )
        with patch("backend.app.MongoRepository") as mock_repo, \
             patch("backend.app.TimeXerModel") as mock_model, \
             patch("backend.app.SegmentMapping") as mock_mapper:
            mock_repo.from_uri.return_value = MagicMock()
            mock_model.from_path.return_value = MagicMock()
            mock_mapper.return_value = MagicMock()
            app = create_app(settings)
            app.config["TESTING"] = True
            yield app.test_client()

    def test_health_endpoint_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_endpoint_returns_json(self, client):
        response = client.get("/health")
        assert response.content_type == "application/json"

    def test_health_endpoint_has_status(self, client):
        response = client.get("/health")
        data = response.get_json()
        assert "status" in data


class TestTrafficEndpoints:
    """Tests for the traffic API endpoints."""

    @pytest.fixture
    def client(self):
        """Create a test client with mocked dependencies."""
        settings = Settings(
            mongo_uri="mongodb://localhost:27017",
            mongo_db_name="TrafficTest",
            mongo_pool_size=10,
            model_path="/tmp/fake_model.pth",
            dynamodb_table="test-road-segments",
            aws_region="us-east-1",
        )
        with patch("backend.app.MongoRepository") as mock_repo, \
             patch("backend.app.TimeXerModel") as mock_model, \
             patch("backend.app.SegmentMapping") as mock_mapper:
            mock_repo.from_uri.return_value = MagicMock()
            mock_model.from_path.return_value = MagicMock()
            mock_mapper.return_value = MagicMock()
            app = create_app(settings)
            app.config["TESTING"] = True
            yield app.test_client()

    def test_segments_endpoint(self, client):
        response = client.get("/api/segments")
        assert response.status_code == 200
        assert response.content_type == "application/json"

    def test_current_endpoint_with_invalid_request(self, client):
        response = client.post("/api/current", json={})
        assert response.status_code == 400

    def test_current_endpoint_with_missing_segment_index(self, client):
        response = client.post("/api/current", json={"segment_index": -1})
        assert response.status_code == 400

    def test_predict_endpoint_with_invalid_request(self, client):
        response = client.post("/api/predict", json={})
        assert response.status_code == 400

    def test_db_notice_endpoint_with_invalid_notice(self, client):
        response = client.post("/api/db_notice", json={"notice": "invalid"})
        assert response.status_code == 400

    def test_db_notice_endpoint_with_valid_notice(self, client):
        response = client.post("/api/db_notice", json={"notice": "update"})
        assert response.status_code == 200