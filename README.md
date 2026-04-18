# TrafficPredictor

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Flask 3.x](https://img.shields.io/badge/Flask-3.x-000?logo=flask)](https://flask.palletsprojects.com/)
[![Next.js 15](https://img.shields.io/badge/Next.js-15-black?logo=next.js)](https://nextjs.org/)
[![Airflow 2.10](https://img.shields.io/badge/Airflow-2.10-017CEE?logo=apacheairflow&logoColor=white)](https://airflow.apache.org/)
[![Terraform 1.5+](https://img.shields.io/badge/Terraform-1.5+-7B42BC?logo=terraform&logoColor=white)](https://www.terraform.io/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![PyTorch](https://img.shields.io/badge/PyTorch-TimeXer-EE4C2C?logo=pytorch&logoColor=white)](https://pytorch.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> Real-time traffic monitoring and transformer-based speed forecasting for Ho Chi Minh City.

---

## Overview

TrafficPredictor is an end-to-end data engineering and machine learning system that:

- **Ingests** live traffic flow data from the HERE Traffic API
- **Processes** it through an automated ETL pipeline (Apache Airflow + PySpark)
- **Serves** speed forecasts via a TimeXer transformer model
- **Visualizes** results on an interactive web dashboard

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           AWS Cloud                                      │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                     ETL Pipeline (Airflow)                       │   │
│  │   HERE API → Extract → S3 (Raw) → Transform (PySpark) → Load   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                  ↓                                       │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    Backend (ECS Fargate)                         │   │
│  │   Flask API + TimeXer Model + MongoDB/DocumentDB                │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                  ↑
┌─────────────────────────────────────────────────────────────────────────┐
│                      Frontend (Vercel)                                   │
│   Next.js 15 + Tailwind CSS + Leaflet Map                               │
└─────────────────────────────────────────────────────────────────────────┘
```

| Component | Stack | Deployment |
|-----------|-------|------------|
| **Frontend** | Next.js 15, Tailwind CSS 4, Leaflet | Vercel |
| **Backend** | Flask 3, PyTorch, Pydantic v2 | AWS ECS Fargate |
| **ETL Pipeline** | Apache Airflow 2.10, PySpark, boto3 | AWS MWAA |
| **Database** | MongoDB / Amazon DocumentDB | AWS DocumentDB |
| **Infrastructure** | Terraform (modular) | AWS |

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker & Docker Compose
- (Optional) AWS CLI for deployment
- (Optional) Terraform >= 1.5 for infrastructure

### 1. Clone the Repository

```bash
git clone https://github.com/vinhky123/TrafficPredictor.git
cd TrafficPredictor
```

### 2. Start Backend + Airflow (Docker)

```bash
# Start all services (backend, Airflow, MongoDB, Postgres, Redis)
make docker-run

# Backend API:       http://localhost:5000
# Airflow UI:        http://localhost:8080  (airflow / airflow)
# MongoDB:           localhost:27017
```

### 3. Start Frontend (local development)

```bash
make frontend-install
make frontend-dev

# Dashboard:         http://localhost:3000
```

### 4. Deploy Infrastructure (Terraform)

```bash
cd infra
terraform init
terraform plan -var-file=environments/dev.tfvars -var="docdb_master_password=<password>"
terraform apply -var-file=environments/dev.tfvars -var="docdb_master_password=<password>"
```

## Development

### Running Tests

```bash
# Backend tests
make backend-test

# Frontend tests
make frontend-test
```

### Code Quality

```bash
# Install pre-commit hooks
make pre-commit-install

# Or run linters manually
make backend-lint
```

### Available Commands

Run `make help` to see all available commands.

## Data Pipeline

The ETL pipeline runs every 5 minutes and follows these stages:

| Stage | Task | Description |
|-------|------|-------------|
| 1 | **Extract** | Fetch real-time traffic flow from HERE API |
| 2 | **Upload** | Store raw JSON snapshot in S3 |
| 3 | **Transform** | PySpark: parse flow data, compute speed (km/h), write Parquet |
| 4 | **Load** | Upsert transformed records into DocumentDB |
| 5 | **Predict** | Trigger TimeXer inference via backend API |

## ML Model — TimeXer

The forecasting engine is a **TimeXer** (Time-series Exogenous Transformer) model:

| Parameter | Value |
|-----------|-------|
| Sequence length | 96 |
| Prediction horizon | 12 |
| Variates | 325 (8 real + padding) |
| Patch length | 12 |
| d_model | 256 |
| Encoder layers | 4 |
| Preprocessing | DWT denoising (db4 wavelet) |

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/api/segments` | List all road segments |
| `POST` | `/api/current` | Get current speed for a segment |
| `POST` | `/api/predict` | Get speed forecast for a segment |
| `POST` | `/api/db_notice` | Trigger batch prediction update |

See [docs/api-reference.md](docs/api-reference.md) for full documentation.

## Project Structure

```
TrafficPredictor/
├── backend/          # Flask REST API + TimeXer inference
│   ├── app/          # Application code
│   │   ├── routes/   # API endpoints
│   │   ├── services/ # Business logic
│   │   ├── models/   # ML model definitions
│   │   ├── repositories/ # Data access layer
│   │   ├── config.py # Configuration
│   │   ├── dependencies.py # Dependency injection
│   │   └── errors.py # Error handling
│   ├── Dockerfile
│   └── requirements.txt
├── web/              # Next.js dashboard with Leaflet map
│   ├── src/
│   │   ├── app/      # Next.js app router
│   │   ├── components/ # React components
│   │   ├── lib/      # API client & types
│   │   └── hooks/    # Custom React hooks
│   └── package.json
├── airflow/          # Airflow DAGs + custom operators
│   ├── dags/         # ETL pipeline definitions
│   └── plugins/      # Custom operators
├── infra/            # Terraform modules
│   ├── modules/      # Reusable infrastructure modules
│   └── environments/ # Environment-specific configs
├── tests/            # Test suite
│   ├── unit/         # Unit tests
│   └── integration/  # Integration tests
├── docs/             # Documentation
├── docker-compose.yml
├── Makefile
└── pyproject.toml
```

## Component Documentation

- [Backend README](backend/README.md) — Flask API setup, endpoints, Docker
- [Frontend README](web/README.md) — Next.js local dev, Vercel deployment
- [Airflow README](airflow/README.md) — DAG documentation, Airflow Variables
- [Infrastructure README](infra/README.md) — Terraform modules, deployment steps

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is for portfolio and educational purposes. See [LICENSE](LICENSE) for details.

## Acknowledgments

- [HERE Technologies](https://developer.here.com/) for traffic data API
- [TimeXer](https://github.com/thuml/TimeXer) paper authors for the model architecture
- OpenStreetMap contributors for map data