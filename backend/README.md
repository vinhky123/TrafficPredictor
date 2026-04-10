# Backend — Flask API

REST API that serves real-time traffic speeds and transformer-based forecasts for Ho Chi Minh City.

## Tech Stack

| Layer | Tool |
|-------|------|
| Framework | Flask 3 + flask-cors |
| Database | MongoDB (via pymongo) |
| ML Model | TimeXer (PyTorch) |
| Validation | Pydantic v2 |
| Preprocessing | PyWavelets (DWT denoising) |

## Project Structure

```
app/
├── __init__.py          # create_app() factory
├── app.py               # WSGI entry point
├── config.py            # Settings from environment
├── errors.py            # Custom exception hierarchy
├── schemas.py           # Pydantic request/response models
├── utils.py             # Coordinate mapping + data preprocessing
├── models/
│   ├── model.py         # TimeXer transformer architecture
│   └── timexer_model.py # Model loader wrapper
├── repositories/
│   └── mongo_repository.py  # MongoDB data access
├── routes/
│   ├── health_routes.py     # GET /health
│   └── traffic_routes.py    # POST /api/current, /api/predict, /api/db_notice
└── services/
    ├── traffic_service.py      # Current speed + prediction retrieval
    └── prediction_service.py   # Batch inference pipeline
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/api/current` | Current speed (km/h) for a coordinate |
| `POST` | `/api/predict` | Latest prediction for a coordinate |
| `POST` | `/api/db_notice` | Trigger batch prediction update |

See [API Reference](../docs/api-reference.md) for request/response examples.

## Local Development

```bash
cp .env.example .env
pip install -r requirements.txt
python -m app.app
```

The server starts on `http://localhost:5000`.

## Docker

```bash
docker build -t traffic-backend .
docker run -p 5000:5000 --env-file .env traffic-backend
```

Or use the root `docker-compose.yml` to start the full stack.
