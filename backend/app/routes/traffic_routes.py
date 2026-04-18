"""Traffic API routes.

This module defines the REST API endpoints for traffic data and predictions.
All routes use the dependency injection pattern to access services.
"""

from __future__ import annotations

import json
import logging

from flask import Blueprint, jsonify, request

from backend.app.dependencies import get_service_container
from backend.app.errors import BadRequest, NotFound
from backend.app.schemas import SegmentRequest

logger = logging.getLogger(__name__)

traffic_bp = Blueprint("traffic", __name__)


@traffic_bp.get("/segments")
def list_segments():
    """Return all registered road segments (index, name, shape) for the frontend.

    Returns:
        JSON response with list of road segments.
    """
    container = get_service_container()
    mapper = container.segment_mapping
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

    logger.info("Listed %d road segments", len(result))
    return jsonify(result), 200


@traffic_bp.post("/current")
def current_speed():
    """Get current speed for a road segment.

    Expects JSON body with segment_index.
    Returns current speed in km/h.

    Returns:
        JSON response with segment_index and current speed.

    Raises:
        BadRequest: If request body is invalid.
        NotFound: If segment is not found.
    """
    try:
        payload = SegmentRequest.model_validate(request.get_json(silent=True) or {})
    except Exception as e:
        logger.warning("Invalid request body for /current: %s", e)
        raise BadRequest("Invalid request body")

    container = get_service_container()
    traffic_service = container.traffic_service
    speed = traffic_service.get_current_speed_kmh(payload.segment_index)

    if speed is None:
        raise NotFound(f"Segment {payload.segment_index} not found")

    logger.info("Current speed requested for segment %d: %s km/h", payload.segment_index, speed)
    return jsonify({"segment_index": payload.segment_index, "current": speed}), 200


@traffic_bp.post("/predict")
def predict():
    """Get speed prediction for a road segment.

    Expects JSON body with segment_index.
    Returns current speed and predicted speeds for next 60 minutes.

    Returns:
        JSON response with segment_index, name, current speed, and predictions.

    Raises:
        BadRequest: If request body is invalid.
        NotFound: If segment is not found.
    """
    try:
        payload = SegmentRequest.model_validate(request.get_json(silent=True) or {})
    except Exception as e:
        logger.warning("Invalid request body for /predict: %s", e)
        raise BadRequest("Invalid request body")

    container = get_service_container()
    traffic_service = container.traffic_service
    name, current_speed_val, predict_speed = traffic_service.get_prediction(payload.segment_index)

    if name is None and current_speed_val is None:
        raise NotFound(f"Segment {payload.segment_index} not found")

    logger.info(
        "Prediction requested for segment %d (%s): current=%s",
        payload.segment_index, name, current_speed_val,
    )
    return jsonify({
        "segment_index": payload.segment_index,
        "name": name,
        "current": current_speed_val,
        "predict": predict_speed,
    }), 200


@traffic_bp.post("/db_notice")
def db_notice():
    """Trigger batch prediction update.

    This endpoint is called by the Airflow DAG after ETL completion
    to trigger batch predictions for all segments.

    Returns:
        JSON response with number of predictions inserted.

    Raises:
        BadRequest: If notice value is not 'update'.
    """
    data = request.get_json(silent=True) or {}
    if data.get("notice") != "update":
        raise BadRequest("Invalid notice value. Expected 'update'")

    container = get_service_container()
    prediction_service = container.prediction_service
    inserted = prediction_service.update_predictions()

    logger.info("Batch prediction triggered via db_notice: inserted %d predictions", inserted)
    return jsonify({"notice": "Updating DB and predicting", "inserted": inserted}), 200