from __future__ import annotations

from dataclasses import dataclass

from ..repositories.mongo_repository import MongoRepository
from ..utils import Mapping


@dataclass(frozen=True)
class TrafficService:
    repo: MongoRepository
    mapper: Mapping

    def get_current_speed_kmh(self, lat: float, lng: float) -> float | None:
        name = self.mapper.get_location_name((lat, lng))
        if not name:
            return None
        speed_ms = self.repo.get_latest_speed(name)
        if speed_ms is None:
            return None
        return round(float(speed_ms) * 3.6, 2)

    def get_prediction(self, lat: float, lng: float) -> tuple[str | None, float | None, list[float] | None]:
        name = self.mapper.get_location_name((lat, lng))
        current = self.get_current_speed_kmh(lat, lng)
        if not name:
            return None, current, None
        pred = self.repo.get_latest_prediction(name)
        return name, current, pred

