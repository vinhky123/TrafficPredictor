# Architecture

This document describes the system architecture, data flow, and component responsibilities of the TrafficPredictor platform.

## System Overview

TrafficPredictor is a serverless three-tier system designed for real-time traffic monitoring and forecasting in Ho Chi Minh City:

1. **Data Ingestion & ETL** — AWS Step Functions orchestrate a pipeline of Lambda functions that extract traffic data from the HERE Traffic API, transform it, and load it into DynamoDB.
2. **Backend API** — A Flask application (wrapped as a Lambda handler via `aws-lambda-wsgi`) serves traffic data and runs inference using a TimeXer transformer model.
3. **Frontend Dashboard** — A Next.js application with an interactive Leaflet map, deployed on Vercel, consuming real-time updates via Server-Sent Events.

## Architecture Diagram

```mermaid
flowchart TB
  subgraph ext ["External"]
    HERE["HERE Traffic Flow API"]
    Browser["Browser / User"]
    Vercel["Vercel (Next.js)"]
  end

  subgraph aws ["AWS Cloud"]
    direction TB

    subgraph api ["API Layer"]
      APIGW["API Gateway REST"]
      LambdaAPI["Lambda: REST API (Flask + aws-lambda-wsgi)"]
      LambdaSSE["Lambda: SSE Broadcast"]
    end

    subgraph pipeline ["ETL Pipeline (Step Function)"]
      direction TB
      EV["EventBridge (schedule: */5 * * * *)"] --> SF["Step Function"]

      subgraph sf_extract ["Extract"]
        L1["Lambda: Extract (HERE API to S3)"]
      end

      subgraph sf_transform ["Transform"]
        L2["Lambda: Transform (Parse, Register, JSONL)"]
      end

      subgraph sf_load ["Load"]
        L3["Lambda: Load (JSONL to DynamoDB)"]
      end

      subgraph sf_predict ["Predict"]
        L4["Lambda: Predict (PyTorch Container)"]
      end

      L1 --> L2 --> L3 --> L4
    end

    subgraph storage ["Storage"]
      D1["DynamoDB: Segments (PK: shape_hash)"]
      D2["DynamoDB: Speeds (PK: seg, SK: ts)"]
      D3["DynamoDB: Predictions (PK: seg, SK: ts)"]
      D4["DynamoDB: WS Connections (PK: connection_id)"]
      S3RAW["S3: Raw HERE JSON"]
      S3PROC["S3: Processed JSONL"]
    end

    SNS["SNS Topic (pipeline-notifications)"]
  end

  HERE -- "HTTP GET /v7/flow" --> L1

  L1 -- "writes" --> S3RAW
  L2 -- "reads/writes" --> S3RAW
  L2 -- "registers" --> D1
  L2 -- "writes" --> S3PROC
  L3 -- "reads" --> S3PROC
  L3 -- "batch writes" --> D2
  L4 -- "reads recent" --> D2
  L4 -- "writes" --> D3

  L4 --> SNS
  SNS --> LambdaSSE

  LambdaAPI -- "reads" --> D1
  LambdaAPI -- "reads" --> D2
  LambdaAPI -- "reads" --> D3

  Browser -- "open app" --> Vercel
  Vercel -- "REST API (HTTPS)" --> APIGW
  APIGW --> LambdaAPI

  LambdaSSE -- "SSE" --> Vercel
```

## Component Details

### ETL Pipeline (Step Functions)

The pipeline runs on a 5-minute schedule, orchestrated by AWS Step Functions:

| Step | Component | Input | Processing | Output |
|------|-----------|-------|-----------|--------|
| Extract | Lambda | HERE API | HTTP request with circle query around HCMC | Raw JSON → S3 |
| Transform | Lambda | Raw JSON from S3 | Parse flow data, filter road segments, convert speed m/s to km/h, add metadata | Structured records |
| Load | Lambda | Transformed records | Batch upsert into DynamoDB | DynamoDB table |
| Predict | Lambda | Latest 96 readings | DWT denoising → TimeXer inference → store forecasts | Predictions in DynamoDB |

### Backend (Flask + Lambda)

The backend is a Flask application wrapped in an `aws-lambda-wsgi` handler for Lambda + API Gateway. It follows a layered architecture:

```
API Gateway → Lambda (aws-lambda-wsgi) → Flask → Services → Repositories → DynamoDB
                                                    → Models (TimeXer)
```

- **Routes** handle HTTP request/response, validation via Pydantic schemas.
- **Services** contain business logic (speed conversion, prediction orchestration).
- **Repositories** abstract database access (DynamoDB via boto3 + MongoRepository for local dev).
- **Models** encapsulate the TimeXer neural network and inference logic.

#### Prediction Flow

1. Step Functions triggers the Predict Lambda after new data is loaded.
2. Predict Lambda fetches the last 96 speed readings per location from DynamoDB.
3. Data is preprocessed: DWT denoising (db4 wavelet) and zero-padding to 325 variates.
4. TimeXer model runs inference, producing 12-step forecasts.
5. Predictions are written back to DynamoDB.
6. An SNS notification triggers SSE updates to connected browser clients.

### Frontend (Next.js)

- **Server-side rendering** for the page shell (layout, metadata).
- **Client-side** interactive map (Leaflet loaded via `next/dynamic` to skip SSR).
- **Sidebar** with location search, selection, and forecast display.
- **SSE client** (`EventSource`) receives real-time updates from the backend.
- Communicates with backend via `NEXT_PUBLIC_API_URL` environment variable.

### Infrastructure (Terraform)

All AWS resources are provisioned via Terraform modules:

| Module | Resources |
|--------|-----------|
| `networking` | VPC, 2+ AZs, public/private subnets, NAT gateway, route tables |
| `lambda` | Lambda functions for API + ETL + predictions |
| `api_gateway` | REST API with resource paths, methods, and Lambda integration |
| `step_functions` | State machine for ETL pipeline |
| `dynamodb` | DynamoDB tables for traffic data, segments, predictions |
| `sns` | Notification topics for real-time updates |
| `s3` | Data bucket (versioned, encrypted) |

## Network Topology

```mermaid
flowchart TB
  subgraph vpc [VPC 10.0.0.0/16]
    subgraph private [Private Subnets]
      Lambda["Lambda (VPC mode)"]
      DynDB["DynamoDB (VPC Endpoint)"]
    end
    Lambda --> DynDB
  end
  Internet --> APIGW["API Gateway"]
  APIGW --> Lambda
```

## Monitoring Locations

The system monitors 8 traffic points across Ho Chi Minh City:

| Location | Coordinates |
|----------|-------------|
| Cau Sai Gon (Saigon Bridge) | 10.7989, 106.7270 |
| Cau Rach Chiec | 10.8132, 106.7568 |
| Cau Dien Bien Phu | 10.7934, 106.7004 |
| Dai Hoc Bach Khoa (BKU) | 10.7721, 106.6576 |
| Cong Vien Hoang Van Thu | 10.8018, 106.6649 |
| Vong Xoay Dan Chu | 10.7779, 106.6813 |
| Cong Vien Le Thi Rieng | 10.7855, 106.6633 |
| Duong Truong Chinh | 10.8168, 106.6320 |
