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
backend/app/
├── __init__.py           # App factory with logging & error handlers
├── app.py                # Entry point
├── config.py             # Settings dataclass
├── dependencies.py       # Service container for DI
├── errors.py             # Custom exceptions & error handlers
├── schemas.py            # Pydantic request/response models
├── utils.py              # Utility classes (SegmentMapping, DataForModel)
├── models/               # ML model definitions
├── repositories/         # Data access layer
├── routes/               # API endpoints
└── services/             # Business logic layer
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

## Working with Airflow

### DAG Structure

```
airflow/dags/
└── traffic_etl_dag.py    # Main ETL pipeline

airflow/plugins/
└── operators/            # Custom operators
```

### Adding a New Task

1. Define Python callable:

```python
def my_new_task(**context):
    """Task logic here."""
    logger.info("Running my new task")
    return {"result": "success"}
```

2. Add to DAG:

```python
t_new = PythonOperator(
    task_id="my_new_task",
    python_callable=my_new_task,
)

# Set dependencies
t_existing >> t_new
```

### Testing DAG Locally

```bash
# Start Airflow
docker compose up -d airflow-webserver airflow-scheduler airflow-worker

# Access UI at http://localhost:8080
# Login: airflow / airflow

# Trigger DAG manually or wait for schedule
```

### Airflow Variables

Set required variables in Airflow UI (Admin → Variables):

| Variable | Description | Example |
|----------|-------------|---------|
| `HERE_API_KEY` | HERE Traffic API key | `your-api-key` |
| `MONGODB_URI` | MongoDB connection string | `mongodb://mongo:27017` |
| `MONGODB_DB_NAME` | Database name | `Traffic` |
| `S3_BUCKET` | S3 bucket for data | `traffic-data` |
| `DYNAMODB_TABLE` | Segment registry table | `road-segments` |
| `BACKEND_URL` | Flask API URL | `http://backend:5000` |
| `TELEGRAM_BOT_TOKEN` | Notification bot token | `123456:ABC...` |
| `TELEGRAM_CHAT_ID` | Notification chat ID | `-123456789` |

## Working with Infrastructure

### Terraform Modules

```
infra/
├── modules/
│   ├── networking/    # VPC, subnets, route tables
│   ├── ecr/           # Container registries
│   ├── ecs/           # Fargate cluster + service
│   ├── mwaa/          # Managed Airflow
│   ├── documentdb/    # DocumentDB cluster
│   ├── dynamodb/      # DynamoDB tables
│   └── s3/            # S3 buckets
├── environments/
│   ├── dev.tfvars     # Dev environment config
│   └── prod.tfvars    # Prod environment config
```

### Deploying Changes

```bash
cd infra

# Initialize
terraform init

# Preview changes
terraform plan -var-file=environments/dev.tfvars \
  -var="docdb_master_password=YOUR_PASSWORD"

# Apply
terraform apply -var-file=environments/dev.tfvars \
  -var="docdb_master_password=YOUR_PASSWORD"
```

### State Management

The project uses remote state storage:

```hcl
# providers.tf
terraform {
  backend "s3" {
    bucket = "trafficpredictor-terraform-state"
    key    = "infrastructure/terraform.tfstate"
    region = "ap-southeast-1"
  }
}
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