"""Unit tests for Pydantic schemas."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from backend.app.schemas import SegmentRequest


class TestSegmentRequest:
    """Tests for the SegmentRequest schema."""

    def test_valid_request(self):
        req = SegmentRequest(segment_index=1)
        assert req.segment_index == 1

    def test_invalid_segment_index_zero(self):
        with pytest.raises(ValidationError):
            SegmentRequest(segment_index=0)

    def test_invalid_segment_index_negative(self):
        with pytest.raises(ValidationError):
            SegmentRequest(segment_index=-1)

    def test_large_segment_index(self):
        req = SegmentRequest(segment_index=999999)
        assert req.segment_index == 999999