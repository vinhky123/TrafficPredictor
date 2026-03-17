from __future__ import annotations

from pydantic import BaseModel, Field


class Location(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)


class LocationRequest(BaseModel):
    location: Location


class CurrentResponse(BaseModel):
    current: float


class PredictResponse(BaseModel):
    name: str | None
    current: float
    predict: list[float] | None

