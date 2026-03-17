from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request
from pydantic import ValidationError

from ..config import Settings
from ..repositories.mongo_repository import MongoRepository
from ..schemas import LocationRequest
from ..services.prediction_service import PredictionService
from ..services.traffic_service import TrafficService
from ..utils import Mapping
from ..models.timexer_model import TimeXerModel


traffic_bp = Blueprint("traffic", __name__)


def _services() -> tuple[TrafficService, PredictionService]:
    settings: Settings = current_app.config["APP_SETTINGS"]
    mapper = Mapping()

    # For a portfolio repo we allow running without actual DB/credentials.
    if not settings.mongo_uri:
        repo = MongoRepository.from_uri("mongodb://localhost:27017", settings.mongo_db_name)
    else:
        repo = MongoRepository.from_uri(settings.mongo_uri, settings.mongo_db_name, settings.mongo_pool_size)

    model = TimeXerModel.from_path(settings.model_path)

    traffic_service = TrafficService(repo=repo, mapper=mapper)
    prediction_service = PredictionService(repo=repo, mapper=mapper, model=model)
    return traffic_service, prediction_service


@traffic_bp.post("/current")
def current_speed():
    try:
        payload = LocationRequest.model_validate(request.get_json(force=True))
    except ValidationError as e:
        return jsonify({"error": "Invalid request body", "details": e.errors()}), 400

    traffic_service, _ = _services()
    speed = traffic_service.get_current_speed_kmh(payload.location.lat, payload.location.lng)
    if speed is None:
        return jsonify({"error": "Location not found"}), 404

    return jsonify({"current": speed}), 200


@traffic_bp.post("/predict")
def predict():
    try:
        payload = LocationRequest.model_validate(request.get_json(force=True))
    except ValidationError as e:
        return jsonify({"error": "Invalid request body", "details": e.errors()}), 400

    traffic_service, _ = _services()
    name, current_speed, predict_speed = traffic_service.get_prediction(
        payload.location.lat, payload.location.lng
    )
    if current_speed is None:
        return jsonify({"error": "Location not found"}), 404

    return jsonify(
        {
            "name": name,
            "current": current_speed,
            "predict": predict_speed,
        }
    ), 200


@traffic_bp.post("/db_notice")
def db_notice():
    data = request.get_json(silent=True) or {}
    if data.get("notice") != "update":
        return jsonify({"error": "Invalid request"}), 400

    _, prediction_service = _services()
    inserted = prediction_service.update_predictions()
    return jsonify({"notice": "Updating DB and predicting", "inserted": inserted}), 200

