# TrafficPredictor

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Flask 3.x](https://img.shields.io/badge/Flask-3.x-000?logo=flask)](https://flask.palletsprojects.com/)
[![Next.js 15](https://img.shields.io/badge/Next.js-15-black?logo=next.js)](https://nextjs.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-TimeXer-EE4C2C?logo=pytorch&logoColor=white)](https://pytorch.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Terraform 1.5+](https://img.shields.io/badge/Terraform-1.5+-7B42BC?logo=terraform&logoColor=white)](https://www.terraform.io/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)

> Real-time traffic monitoring and transformer-based speed forecasting for Ho Chi Minh City.

---

## Overview

TrafficPredictor is a serverless data engineering and machine learning system that:

- **Ingests** live traffic flow data from the HERE Traffic API via Step Functions
- **Processes** it through a serverless Extract → Transform → Load → Predict pipeline
- **Serves** speed forecasts via a TimeXer transformer model (Lambda + API Gateway)
- **Streams** real-time updates to the browser via Server-Sent Events
- **Visualizes** results on an interactive web dashboard

## Architecture

```
HERE API → Step Function (Extract → Transform → Load → Predict)
            ↕
DynamoDB ← API Gateway → Lambda REST API
            ↕
WebSocket/SNS → Browser (SSE)
```

| Component | Stack | Deployment |
|-----------|-------|------------|
| **Frontend** | Next.js 15, Tailwind CSS 4, Leaflet | Vercel |
| **Backend** | Flask 3, PyTorch, Pydantic v2 | AWS Lambda + API Gateway |
| **ETL Pipeline** | AWS Step Functions, Lambda, boto3 | AWS |
| **Database** | Amazon DynamoDB | AWS |
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

### 2. Start Backend (Docker)

```bash
# Start backend and MongoDB for local development
make docker-run

# Backend API:       http://localhost:5000
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
terraform plan -var-file=environments/dev.tfvars
terraform apply -var-file=environments/dev.tfvars
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

The ETL pipeline runs every 5 minutes via AWS Step Functions:

| Stage | Component | Description |
|-------|-----------|-------------|
| 1 | **Extract** | Lambda fetches real-time traffic flow from HERE API |
| 2 | **Transform** | Lambda parses flow data, computes speed (km/h), enriches metadata |
| 3 | **Load** | Lambda upserts transformed records into DynamoDB |
| 4 | **Predict** | Lambda triggers TimeXer inference and stores forecasts |

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

See [docs/api-reference.md](docs/api-reference.md) for full documentation.

## Project Structure

```
TrafficPredictor/
├── backend/          # Flask REST API + TimeXer inference
│   ├── app/          # Application code
│   │   ├── routes/   # API endpoints
│   │   ├── services/ # Business logic
│   │   ├── models/   # ML model definitions
│   │   ├── repositories/ # Data access layer (MongoDB + DynamoDB)
│   │   ├── config.py # Configuration
│   │   ├── dependencies.py # Dependency injection
│   │   └── errors.py # Error handling
│   ├── lambdas/      # AWS Lambda handlers
│   ├── Dockerfile
│   └── requirements.txt
├── web/              # Next.js dashboard with Leaflet map
│   ├── src/
│   │   ├── app/      # Next.js app router
│   │   ├── components/ # React components
│   │   ├── lib/      # API client & types
│   │   └── hooks/    # Custom React hooks (SSE)
│   └── package.json
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
- [Lambda README](backend/lambdas/README.md) — Lambda structure and deployment
- [Infrastructure README](infra/README.md) — Terraform modules, deployment steps

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is for portfolio and educational purposes. See [LICENSE](LICENSE) for details.

## Acknowledgments

- [HERE Technologies](https://developer.here.com/) for traffic data API
- [TimeXer](https://github.com/thuml/TimeXer) paper authors for the model architecture
- OpenStreetMap contributors for map data
