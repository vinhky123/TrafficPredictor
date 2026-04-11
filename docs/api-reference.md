# API Reference

Base URL: `http://localhost:5000` (local) or the ALB DNS from Terraform output.

## Endpoints

### Health Check

```
GET /health
```

**Response** `200 OK`

```json
{
  "status": "ok"
}
```

---

### List Road Segments

```
GET /api/segments
```

Returns all registered road segments with their shapes (for rendering polylines on the map).

**Response** `200 OK`

```json
[
  {
    "segment_index": 1,
    "name": "Nguyen Van Linh",
    "shape": [
      { "lat": 10.7321, "lng": 106.6958 },
      { "lat": 10.7325, "lng": 106.6962 }
    ]
  }
]
```

---

### Get Current Speed

```
POST /api/current
```

Returns the latest recorded speed (in km/h) for a road segment.

**Request Body**

```json
{
  "segment_index": 1
}
```

**Response** `200 OK`

```json
{
  "segment_index": 1,
  "current": 32.45
}
```

**Error Response** `404 Not Found`

```json
{
  "error": "Segment not found"
}
```

---

### Get Prediction

```
POST /api/predict
```

Returns the current speed and the latest forecast (12 future time-steps, each representing a 5-minute interval) for a road segment.

**Request Body**

```json
{
  "segment_index": 1
}
```

**Response** `200 OK`

```json
{
  "segment_index": 1,
  "name": "Nguyen Van Linh",
  "current": 32.45,
  "predict": [31.2, 30.8, 29.5, 28.1, 27.3, 26.9, 27.5, 28.0, 29.1, 30.2, 31.0, 31.8]
}
```

Each value in `predict` is the forecasted speed in km/h for the next 5-minute window.

**Error Response** `404 Not Found`

```json
{
  "error": "Segment not found"
}
```

---

### Trigger Batch Prediction

```
POST /api/db_notice
```

Triggers the backend to fetch the latest 96 time-steps for all registered road segments, run batch TimeXer inference, and store predictions in the database. Typically called by the Airflow pipeline after new data is loaded.

**Request Body**

```json
{
  "notice": "update"
}
```

**Response** `200 OK`

```json
{
  "notice": "Updating DB and predicting",
  "inserted": 142
}
```

---

## Road Segments

Road segments are dynamically registered by the ETL pipeline. Each segment is identified by a `segment_index` (integer) stored in DynamoDB. The API no longer uses fixed lat/lng coordinates -- use `GET /api/segments` to discover available segments and their shapes.
