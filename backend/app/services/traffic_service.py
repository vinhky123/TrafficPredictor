from __future__ import annotations

from dataclasses import dataclass

from ..repositories.mongo_repository import MongoRepository
from ..utils import SegmentMapping


@dataclass(frozen=True)
class TrafficService:
    repo: MongoRepository
    mapper: SegmentMapping

    def get_current_speed_kmh(self, segment_index: int) -> float | None:
        seg = self.mapper.get_segment_by_index(segment_index)
        if not seg:
            return None
        speed_ms = self.repo.get_latest_speed(segment_index)
        if speed_ms is None:
            return None
        return round(float(speed_ms) * 3.6, 2)

    def get_prediction(self, segment_index: int) -> tuple[str | None, float | None, list[float] | None]:
        seg = self.mapper.get_segment_by_index(segment_index)
        if not seg:
            return None, None, None
        name = seg.get("name")
        current = self.get_current_speed_kmh(segment_index)
        pred = self.repo.get_latest_prediction(segment_index)
        return name, current, pred
