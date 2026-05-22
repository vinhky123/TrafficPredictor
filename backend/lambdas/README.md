# Lambda Functions

This directory contains AWS Lambda handlers for the serverless ETL pipeline and API endpoint.

## Structure

```
lambdas/
├── extract.py      # Fetches traffic data from HERE API, stores raw JSON in S3
├── transform.py    # Parses raw flow data, computes speed, enriches metadata
├── load.py         # Upserts transformed records into DynamoDB
├── predict.py      # Runs TimeXer inference, stores forecasts in DynamoDB
└── handler.py      # API Gateway entry point (wraps Flask via aws-lambda-wsgi)
```

## Pipeline

The Step Functions state machine invokes these functions in sequence:

```
extract → transform → load → predict
```

Each function receives the previous function's output as its input payload.

## Local Testing

Test individual Lambda handlers by invoking them directly:

```bash
python -c "from lambdas.extract import handler; print(handler({}, None))"
```
