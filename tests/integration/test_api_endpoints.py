from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask

from backend.app import create_app
from backend.app.config import Settings


class TestHealthEndpoint:
    @pytest.fixture
    def client(self):
        settings = Settings(
            mongo_uri="mongodb://localhost:27017",
            mongo_db_name="TrafficTest",
            mongo_pool_size=10,
            model_path="/tmp/fake_model.pth",
            segments_table="test-segments",
            speeds_table="test-speeds",
            predictions_table="test-predictions",
            aws_region="us-east-1",
        )
        with patch("backend.app.repositories.dynamodb_repository.boto3.resource") as mock_resource:
            mock_resource.return_value = MagicMock()
            with patch("backend.app.dependencies.boto3.resource") as mock_dep:
                mock_dep.return_value = MagicMock()
                with patch("backend.app.TimeXerModel") as mock_model:
                    mock_model.from_path.return_value = MagicMock()
                    with patch("backend.app.SegmentMapping") as mock_mapper:
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
    @pytest.fixture
    def client(self):
        settings = Settings(
            mongo_uri="mongodb://localhost:27017",
            mongo_db_name="TrafficTest",
            mongo_pool_size=10,
            model_path="/tmp/fake_model.pth",
            segments_table="test-segments",
            speeds_table="test-speeds",
            predictions_table="test-predictions",
            aws_region="us-east-1",
        )
        with patch("backend.app.repositories.dynamodb_repository.boto3.resource") as mock_resource:
            mock_resource.return_value = MagicMock()
            with patch("backend.app.dependencies.boto3.resource") as mock_dep:
                mock_dep.return_value = MagicMock()
                with patch("backend.app.TimeXerModel") as mock_model:
                    mock_model.from_path.return_value = MagicMock()
                    with patch("backend.app.SegmentMapping") as mock_mapper:
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
