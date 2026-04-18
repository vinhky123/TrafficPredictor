"""Error handling module for the TrafficPredictor backend.

This module defines custom exceptions with HTTP status codes and provides
Flask error handlers for consistent API error responses.
"""

from __future__ import annotations

from typing import Any

from flask import Flask, jsonify


class AppError(Exception):
    """Base exception for the application."""

    def __init__(self, message: str = "An error occurred", status_code: int = 500, extra: dict | None = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.extra = extra or {}


class BadRequest(AppError):
    """Exception raised for invalid requests (400)."""

    def __init__(self, message: str = "Bad request", extra: dict | None = None):
        super().__init__(message=message, status_code=400, extra=extra)


class NotFound(AppError):
    """Exception raised when a resource is not found (404)."""

    def __init__(self, message: str = "Resource not found", extra: dict | None = None):
        super().__init__(message=message, status_code=404, extra=extra)


class UpstreamError(AppError):
    """Exception raised when an external service fails (502)."""

    def __init__(self, message: str = "Upstream service error", extra: dict | None = None):
        super().__init__(message=message, status_code=502, extra=extra)


class ServiceUnavailable(AppError):
    """Exception raised when a service is unavailable (503)."""

    def __init__(self, message: str = "Service unavailable", extra: dict | None = None):
        super().__init__(message=message, status_code=503, extra=extra)


class ValidationError(AppError):
    """Exception raised for validation failures (422)."""

    def __init__(self, message: str = "Validation error", extra: dict | None = None):
        super().__init__(message=message, status_code=422, extra=extra)


def register_error_handlers(app: Flask) -> None:
    """Register error handlers for the Flask application.

    Args:
        app: The Flask application instance.
    """

    @app.errorhandler(BadRequest)
    def handle_bad_request(error: BadRequest):
        return jsonify({
            "error": "Bad Request",
            "message": error.message,
            **({"details": error.extra} if error.extra else {}),
        }), error.status_code

    @app.errorhandler(NotFound)
    def handle_not_found(error: NotFound):
        return jsonify({
            "error": "Not Found",
            "message": error.message,
            **({"details": error.extra} if error.extra else {}),
        }), error.status_code

    @app.errorhandler(ValidationError)
    def handle_validation_error(error: ValidationError):
        return jsonify({
            "error": "Validation Error",
            "message": error.message,
            **({"details": error.extra} if error.extra else {}),
        }), error.status_code

    @app.errorhandler(UpstreamError)
    def handle_upstream_error(error: UpstreamError):
        return jsonify({
            "error": "Upstream Error",
            "message": error.message,
            **({"details": error.extra} if error.extra else {}),
        }), error.status_code

    @app.errorhandler(ServiceUnavailable)
    def handle_service_unavailable(error: ServiceUnavailable):
        return jsonify({
            "error": "Service Unavailable",
            "message": error.message,
            **({"details": error.extra} if error.extra else {}),
        }), error.status_code

    @app.errorhandler(AppError)
    def handle_app_error(error: AppError):
        return jsonify({
            "error": "Internal Server Error",
            "message": error.message,
            **({"details": error.extra} if error.extra else {}),
        }), error.status_code

    @app.errorhandler(404)
    def handle_404(error):
        return jsonify({
            "error": "Not Found",
            "message": "The requested resource was not found",
        }), 404

    @app.errorhandler(405)
    def handle_405(error):
        return jsonify({
            "error": "Method Not Allowed",
            "message": "The HTTP method is not allowed for this endpoint",
        }), 405

    @app.errorhandler(500)
    def handle_500(error):
        return jsonify({
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
        }), 500