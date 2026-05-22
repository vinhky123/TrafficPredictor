"""Dependency injection module for the TrafficPredictor backend.

This module provides a centralized way to create and cache service instances,
ensuring that expensive resources like ML models and database connections are
only created once per application lifecycle.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from flask import current_app

from backend.app.config import Settings

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from backend.app.models.timexer_model import TimeXerModel
    from backend.app.repositories.dynamodb_repository import DynamoDBRepository
    from backend.app.services.prediction_service import PredictionService
    from backend.app.services.traffic_service import TrafficService
    from backend.app.utils import SegmentMapping


@dataclass
class ServiceContainer:
    """Container for application services with lazy initialization."""

    _settings: Settings
    _db_repo: DynamoDBRepository | None = field(default=None, init=False)
    _segment_mapping: SegmentMapping | None = field(default=None, init=False)
    _timexer_model: TimeXerModel | None = field(default=None, init=False)
    _traffic_service: TrafficService | None = field(default=None, init=False)
    _prediction_service: PredictionService | None = field(default=None, init=False)

    @property
    def db_repo(self) -> DynamoDBRepository:
        if self._db_repo is None:
            from backend.app.repositories.dynamodb_repository import DynamoDBRepository

            self._db_repo = DynamoDBRepository(
                segments_table=self._settings.segments_table,
                speeds_table=self._settings.speeds_table,
                predictions_table=self._settings.predictions_table,
                region=self._settings.aws_region,
            )
            logger.info("DynamoDB repository initialized")
        return self._db_repo

    @property
    def segment_mapping(self) -> SegmentMapping:
        if self._segment_mapping is None:
            from backend.app.utils import SegmentMapping

            self._segment_mapping = SegmentMapping(
                table_name=self._settings.segments_table,
                region=self._settings.aws_region,
            )
            logger.info("Segment mapping initialized")
        return self._segment_mapping

    @property
    def timexer_model(self) -> TimeXerModel:
        if self._timexer_model is None:
            from backend.app.models.timexer_model import TimeXerModel

            self._timexer_model = TimeXerModel.from_path(self._settings.model_path)
            logger.info("TimeXer model loaded from %s", self._settings.model_path)
        return self._timexer_model

    @property
    def traffic_service(self) -> TrafficService:
        if self._traffic_service is None:
            from backend.app.services.traffic_service import TrafficService

            self._traffic_service = TrafficService(
                repo=self.db_repo,
                mapper=self.segment_mapping,
            )
            logger.info("Traffic service initialized")
        return self._traffic_service

    @property
    def prediction_service(self) -> PredictionService:
        if self._prediction_service is None:
            from backend.app.services.prediction_service import PredictionService

            self._prediction_service = PredictionService(
                repo=self.db_repo,
                mapper=self.segment_mapping,
                model=self.timexer_model,
            )
            logger.info("Prediction service initialized")
        return self._prediction_service

    def close(self) -> None:
        pass


# Global service container instance
_service_container: ServiceContainer | None = None


def get_service_container() -> ServiceContainer:
    """Get the global service container instance."""
    global _service_container
    if _service_container is None:
        settings = current_app.config.get("APP_SETTINGS")
        if settings is None:
            settings = Settings.from_env()
        _service_container = ServiceContainer(_settings=settings)
    return _service_container


def reset_service_container() -> None:
    """Reset the global service container (useful for testing)."""
    global _service_container
    if _service_container is not None:
        _service_container.close()
    _service_container = None