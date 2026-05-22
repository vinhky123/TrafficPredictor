import json
import logging
import os
import sys
from datetime import datetime

import boto3
from boto3.dynamodb.conditions import Key
import numpy as np
import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../app"))
from utils import DataForModel
from models.timexer_model import TimeXerModel

logger = logging.getLogger(__name__)


def handler(event, context):
    predictions_table_name = os.environ["PREDICTIONS_TABLE"]
    speeds_table_name = os.environ["SPEEDS_TABLE"]
    segments_table_name = os.environ["SEGMENTS_TABLE"]
    model_path = os.environ.get("MODEL_PATH", "/opt/model/TimeXer.pth")

    ddb = boto3.resource("dynamodb")
    segments_tbl = ddb.Table(segments_table_name)
    speeds_tbl = ddb.Table(speeds_table_name)
    pred_tbl = ddb.Table(predictions_table_name)

    resp = segments_tbl.scan()
    segments = [s for s in resp.get("Items", []) if s.get("shape_hash") != "__COUNTER__"]
    indices = sorted([int(s["segment_index"]) for s in segments])

    history_series: list[list[float]] = []
    valid_indices: list[int] = []

    for idx in indices:
        query_resp = speeds_tbl.query(
            KeyConditionExpression=Key("segment_index").eq(idx),
            ScanIndexForward=False,
            Limit=96,
        )
        speeds = [item.get("speed_kmh") for item in query_resp.get("Items", []) if item.get("speed_kmh") is not None]
        if not speeds:
            continue
        history_series.append(speeds)
        valid_indices.append(idx)

    if not history_series:
        return {"inserted": 0, "message": "No speed data available"}

    max_len = max(len(s) for s in history_series)
    padded = [s + [0.0] * (max_len - len(s)) for s in history_series]

    data = torch.tensor(padded, dtype=torch.float32).T
    processed = DataForModel(data)

    model = TimeXerModel.from_path(model_path)
    predict = model.predict(processed.data).squeeze(0)

    time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    inserted = 0

    for i, idx in enumerate(valid_indices):
        pred_values = [round(float(v), 2) for v in predict[:, i].tolist()]
        pred_tbl.put_item(Item={
            "segment_index": idx,
            "timestamp": time_str,
            "speeds": pred_values,
        })
        inserted += 1

    logger.info("Inserted %d predictions", inserted)

    return {"inserted": inserted}
