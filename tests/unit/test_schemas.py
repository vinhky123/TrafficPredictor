"""Unit tests for Pydantic schemas."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from backend.app.schemas import Location, LocationRequest, SegmentRequest


class TestLocation:
    """Tests for the Location schema."""

    def test_valid_location(self):
        loc = Location(lat=10.776889, lng=106.695278)
        assert loc.lat == 10.776889
        assert loc.lng == 106.695278

    def test_invalid_latitude_too_high(self):
        with pytest.raises(ValidationError):
            Location(lat=91.0, lng=0.0)

    def test_invalid_latitude_too_low(self):
        with pytest.raises(ValidationError):
            Location(lat=-91.0, lng=0.0)

    def test_invalid_longitude_too_high(self):
        with pytest.raises(ValidationError):
            Location(lat=0.0, lng=181.0)

    def test_invalid_longitude_too_low(self):
        with pytest.raises(ValidationError):
            Location(lat=0.0, lng=-181.0)

    def test_boundary_values(self):
        loc = Location(lat=90.0, lng=180.0)
        assert loc.lat == 90.0
        assert loc.lng == 180.0


class TestLocationRequest:
    """Tests for the LocationRequest schema."""

    def test_valid_request(self):
        req = LocationRequest(location={"lat": 10.776889, "lng": 106.695278})
        assert req.location.lat == 10.776889

    def test_invalid_request_missing_location(self):
        with pytest.raises(ValidationError):
            LocationRequest()


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