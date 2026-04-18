"""Unit tests for error handling."""

from __future__ import annotations

import pytest

from backend.app.errors import AppError, BadRequest, NotFound, UpstreamError


class TestAppError:
    """Tests for the base AppError class."""

    def test_app_error_is_exception(self):
        assert issubclass(AppError, Exception)

    def test_app_error_can_be_raised(self):
        with pytest.raises(AppError):
            raise AppError("test error")

    def test_app_error_message(self):
        try:
            raise AppError("test message")
        except AppError as e:
            assert str(e) == "test message"


class TestBadRequest:
    """Tests for the BadRequest error."""

    def test_bad_request_is_app_error(self):
        assert issubclass(BadRequest, AppError)

    def test_bad_request_can_be_raised(self):
        with pytest.raises(BadRequest):
            raise BadRequest("bad request")


class TestNotFound:
    """Tests for the NotFound error."""

    def test_not_found_is_app_error(self):
        assert issubclass(NotFound, AppError)

    def test_not_found_can_be_raised(self):
        with pytest.raises(NotFound):
            raise NotFound("not found")


class TestUpstreamError:
    """Tests for the UpstreamError."""

    def test_upstream_error_is_app_error(self):
        assert issubclass(UpstreamError, AppError)

    def test_upstream_error_can_be_raised(self):
        with pytest.raises(UpstreamError):
            raise UpstreamError("upstream error")