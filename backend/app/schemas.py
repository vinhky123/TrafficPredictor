from __future__ import annotations

from pydantic import BaseModel, Field


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
