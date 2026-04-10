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

### Get Current Speed

```
POST /api/current
```

Returns the latest recorded speed (in km/h) for the given coordinate.

**Request Body**

```json
{
  "location": {
    "lat": 10.772122,
    "lng": 106.657589
  }
}
```

**Response** `200 OK`

```json
{
  "current": 32.45
}
```

**Error Response** `404 Not Found`

```json
{
  "error": "Location not found"
}
```

**Error Response** `400 Bad Request`

```json
{
  "error": "Invalid request body",
  "details": [...]
}
```

---

### Get Prediction

```
POST /api/predict
```

Returns the current speed and the latest forecast (12 future time-steps, each representing a 5-minute interval) for the given coordinate.

**Request Body**

```json
{
  "location": {
    "lat": 10.772122,
    "lng": 106.657589
  }
}
```

**Response** `200 OK`

```json
{
  "name": "BKU",
  "current": 32.45,
  "predict": [31.2, 30.8, 29.5, 28.1, 27.3, 26.9, 27.5, 28.0, 29.1, 30.2, 31.0, 31.8]
}
```

Each value in `predict` is the forecasted speed in km/h for the next 5-minute window.

**Error Response** `404 Not Found`

```json
{
  "error": "Location not found"
}
```

---

### Trigger Batch Prediction

```
POST /api/db_notice
```

Triggers the backend to fetch the latest 96 time-steps for all monitored locations, run TimeXer inference, and store predictions in the database. Typically called by the Airflow pipeline after new data is loaded.

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
  "inserted": 8
}
```

**Error Response** `400 Bad Request`

```json
{
  "error": "Invalid request"
}
```

---

## Monitored Locations

The following coordinates are valid inputs for `/api/current` and `/api/predict`:

| Name | Latitude | Longitude |
|------|----------|-----------|
| SaiGonBride | 10.798905 | 106.726998 |
| RachChiec_Bridge | 10.813187 | 106.756803 |
| DBP_Bridge | 10.793411 | 106.700390 |
| BKU | 10.772122 | 106.657589 |
| HoangVanThu_Park | 10.801761 | 106.664923 |
| DanChu_Roundabout | 10.777923 | 106.681344 |
| LeThiRieng_Park | 10.785456 | 106.663261 |
| TruongChinh_Street | 10.816761 | 106.631952 |

Coordinates must match exactly (the backend uses a fixed mapping table).
