from __future__ import annotations

from pydantic import BaseModel, Field


class Location(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)


class LocationRequest(BaseModel):
    location: Location


class SegmentRequest(BaseModel):
    segment_index: int = Field(..., ge=1)


class CurrentResponse(BaseModel):
    segment_index: int
    current: float


class PredictResponse(BaseModel):
    segment_index: int
    name: str | None
    current: float | None
    predict: list[float] | None


class SegmentItem(BaseModel):
    segment_index: int
    name: str
    shape: list[dict]
