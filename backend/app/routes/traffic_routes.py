from __future__ import annotations

import json

from flask import Blueprint, current_app, jsonify, request
from pydantic import ValidationError

from ..config import Settings
from ..models.timexer_model import TimeXerModel
from ..repositories.mongo_repository import MongoRepository
from ..schemas import SegmentRequest
from ..services.prediction_service import PredictionService
from ..services.traffic_service import TrafficService
from ..utils import SegmentMapping

traffic_bp = Blueprint("traffic", __name__)


def _services() -> tuple[TrafficService, PredictionService]:
    settings: Settings = current_app.config["APP_SETTINGS"]
    mapper = SegmentMapping(settings.dynamodb_table, settings.aws_region)

    if not settings.mongo_uri:
        repo = MongoRepository.from_uri("mongodb://localhost:27017", settings.mongo_db_name)
    else:
        repo = MongoRepository.from_uri(settings.mongo_uri, settings.mongo_db_name, settings.mongo_pool_size)

    model = TimeXerModel.from_path(settings.model_path)

    traffic_service = TrafficService(repo=repo, mapper=mapper)
    prediction_service = PredictionService(repo=repo, mapper=mapper, model=model)
    return traffic_service, prediction_service


@traffic_bp.get("/segments")
def list_segments():
    """Return all registered road segments (index, name, shape) for the frontend."""
    settings: Settings = current_app.config["APP_SETTINGS"]
    mapper = SegmentMapping(settings.dynamodb_table, settings.aws_region)
    segments = mapper.get_all_segments()

    result = []
    for seg in segments:
        shape_raw = seg.get("shape", "[]")
        shape = json.loads(shape_raw) if isinstance(shape_raw, str) else shape_raw
        result.append({
            "segment_index": int(seg["segment_index"]),
            "name": seg.get("name", ""),
            "shape": shape,
        })

    return jsonify(result), 200


@traffic_bp.post("/current")
def current_speed():
    try:
        payload = SegmentRequest.model_validate(request.get_json(force=True))
    except ValidationError as e:
        return jsonify({"error": "Invalid request body", "details": e.errors()}), 400

    traffic_service, _ = _services()
    speed = traffic_service.get_current_speed_kmh(payload.segment_index)
    if speed is None:
        return jsonify({"error": "Segment not found"}), 404

    return jsonify({"segment_index": payload.segment_index, "current": speed}), 200


@traffic_bp.post("/predict")
def predict():
    try:
        payload = SegmentRequest.model_validate(request.get_json(force=True))
    except ValidationError as e:
        return jsonify({"error": "Invalid request body", "details": e.errors()}), 400

    traffic_service, _ = _services()
    name, current_speed_val, predict_speed = traffic_service.get_prediction(payload.segment_index)
    if name is None and current_speed_val is None:
        return jsonify({"error": "Segment not found"}), 404

    return jsonify({
        "segment_index": payload.segment_index,
        "name": name,
        "current": current_speed_val,
        "predict": predict_speed,
    }), 200


@traffic_bp.post("/db_notice")
def db_notice():
    data = request.get_json(silent=True) or {}
    if data.get("notice") != "update":
        return jsonify({"error": "Invalid request"}), 400

    _, prediction_service = _services()
    inserted = prediction_service.update_predictions()
    return jsonify({"notice": "Updating DB and predicting", "inserted": inserted}), 200
