# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Dependency injection pattern for backend services
- Comprehensive test suite (unit + integration)
- CI/CD pipeline with GitHub Actions
- Pre-commit hooks for code quality
- Makefile for common development commands
- pyproject.toml for Python project configuration
- CONTRIBUTING.md with contribution guidelines
- DEVELOPMENT.md with development guide

### Changed
- Refactored backend routes to use service container
- Improved error handling with HTTP status codes
- Enhanced README with architecture diagram
- Updated logging configuration

### Fixed
- Service instantiation on every request (now uses singleton pattern)
- Missing error handlers for Flask application
- Inconsistent input validation across endpoints

## [1.0.0] - 2024-01-01

### Added
- Initial release of TrafficPredictor
- Flask REST API with TimeXer model inference
- Next.js dashboard with Leaflet map visualization
- Airflow ETL pipeline for traffic data ingestion
- Terraform infrastructure modules for AWS deployment
- Docker Compose for local development
- TimeXer transformer model for speed prediction
- HERE Traffic API integration
- MongoDB/DocumentDB data storage
- DynamoDB segment registry
- S3 data lake for raw and processed data