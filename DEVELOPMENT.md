# Development Guide

This guide covers setting up and working with the TrafficPredictor development environment.

## Environment Setup

### System Requirements

- Python 3.11+
- Node.js 20+
- Docker & Docker Compose
- GNU Make (for Makefile commands)
- AWS CLI (for deployment)
- Terraform >= 1.5 (for infrastructure)

### Initial Setup

```bash
# Clone repository
git clone https://github.com/vinhky123/TrafficPredictor.git
cd TrafficPredictor

# Install pre-commit hooks
make pre-commit-install

# Install backend dependencies
make backend-install

# Install frontend dependencies
make frontend-install
```

## Working with the Backend

### Project Structure

```
backend/
├── app/                  # Flask application
│   ├── __init__.py       # App factory with logging & error handlers
│   ├── config.py         # Settings dataclass
│   ├── dependencies.py   # Service container for DI
│   ├── errors/           # Custom exceptions & error handlers
│   ├── schemas.py        # Pydantic request/response models
│   ├── models/           # ML model definitions (TimeXer)
│   ├── repositories/     # DynamoDB data access layer
│   ├── routes/           # API endpoints
│   ├── services/         # Business logic layer
│   └── utils/            # SegmentMapping, DataForModel
├── lambdas/              # AWS Lambda handlers
│   ├── api/              # API Gateway entry (Flask + aws-lambda-wsgi)
│   ├── extract/          # HERE API to S3
│   ├── transform/        # Parse, register segments, JSONL output
│   ├── load/             # JSONL to DynamoDB
│   ├── predict/          # TimeXer inference (container)
│   ├── notify/           # SSE broadcast via SNS
│   ├── websocket/        # WS connect/disconnect
│   └── sse-connect/      # SSE endpoint
└── step-function/        # ASL definition
```

### Adding a New API Endpoint

1. Define request/response schemas in `schemas.py`:

```python
class NewRequest(BaseModel):
    param: str = Field(..., min_length=1)

class NewResponse(BaseModel):
    result: str
```

2. Create service in `services/`:

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class NewService:
    def do_something(self, param: str) -> str:
        return f"Processed: {param}"
```

3. Register route in `routes/`:

```python
from flask import Blueprint, jsonify
from backend.app.dependencies import get_service_container
from backend.app.errors import BadRequest

new_bp = Blueprint("new", __name__)

@new_bp.post("/new")
def new_endpoint():
    try:
        payload = NewRequest.model_validate(request.get_json())
    except Exception as e:
        raise BadRequest(str(e))

    container = get_service_container()
    service = NewService()
    result = service.do_something(payload.param)

    return jsonify({"result": result}), 200
```

4. Register blueprint in `__init__.py`:

```python
from backend.app.routes.new_routes import new_bp
app.register_blueprint(new_bp, url_prefix="/api/new")
```

### Running Backend Locally

```bash
# Start dependencies (MongoDB)
docker compose up -d mongo

# Run Flask app
make backend-run

# Or directly with Python
cd backend && python -m app.app
```

### Debugging

```bash
# Enable debug mode
export FLASK_DEBUG=1
cd backend && python -m app.app

# Access interactive debugger at http://localhost:5000
```

## Working with the Frontend

### Project Structure

```
web/src/
├── app/                  # Next.js App Router
│   ├── layout.tsx        # Root layout with metadata
│   └── page.tsx          # Main page component
├── components/           # React components
│   ├── map-panel.tsx     # Leaflet map component
│   └── sidebar.tsx       # Segment list and controls
├── lib/                  # Utilities
│   ├── api.ts            # API client functions
│   └── types.ts          # TypeScript type definitions
```

### Adding a New Component

1. Create component in `components/`:

```typescript
// components/new-component.tsx
type Props = {
  title: string;
  onAction: () => void;
};

export function NewComponent({ title, onAction }: Props) {
  return (
    <div>
      <h2>{title}</h2>
      <button onClick={onAction}>Click me</button>
    </div>
  );
}
```

2. Use in page:

```typescript
import { NewComponent } from "@/components/new-component";

export default function Page() {
  return <NewComponent title="Hello" onAction={() => {}} />;
}
```

### Running Frontend Locally

```bash
# Start dev server
make frontend-dev

# Or directly
cd web && npm run dev

# Access at http://localhost:3000
```

### Environment Variables

Create `.env.local` in the `web` directory:

```
NEXT_PUBLIC_API_URL=http://localhost:5000
```

## Working with Infrastructure

### Terraform Modules

```
infra/
├── modules/
│   ├── networking/         # VPC, subnets, route tables
│   ├── ecr/                # ECR repos (predict Lambda container)
│   ├── s3/                 # S3 buckets (raw, processed, models, lambdas)
│   ├── dynamodb/           # DynamoDB tables (segments, speeds, predictions, connections)
│   ├── lambda-function/    # Reusable Lambda function module
│   ├── api-gateway/        # REST API Gateway
│   ├── sse-api-gateway/    # SSE API Gateway
│   ├── step-function/      # State machine
│   ├── eventbridge/        # Schedule rule
│   └── sns/                # Notification topic
├── environments/
│   ├── dev.tfvars          # Dev environment config
│   └── prod.tfvars         # Prod environment config
```

### Deploying Changes

```bash
cd infra

# Initialize
terraform init

# Preview changes
terraform plan -var-file=environments/dev.tfvars

# Apply
terraform apply -var-file=environments/dev.tfvars
```

## Testing

### Running All Tests

```bash
make backend-test
```

### Running Specific Tests

```bash
# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v -m integration

# Specific test
pytest tests/unit/test_schemas.py::TestLocation::test_valid_location -v
```

### Writing Tests

Use the fixtures from `conftest.py`:

```python
def test_something(client, mock_mongo_client):
    # Test using mocked dependencies
    response = client.get("/api/segments")
    assert response.status_code == 200
```

## Code Quality

### Linting

```bash
# Python
make backend-lint

# TypeScript
cd web && npm run lint
```

### Formatting

```bash
# Python (via ruff)
ruff format backend/ tests/

# TypeScript (via prettier)
cd web && npx prettier --write src/
```

## Common Issues

### MongoDB Connection Error

Ensure MongoDB is running:

```bash
docker compose up -d mongo
```

### Module Not Found

Ensure you're running commands from project root:

```bash
cd /path/to/TrafficPredictor
```

### Port Conflicts

Check if ports are already in use:

```bash
lsof -i :5000  # Backend
lsof -i :3000  # Frontend
lsof -i :8080  # Airflow
lsof -i :27017 # MongoDB