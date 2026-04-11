from __future__ import annotations

import json
import time
from typing import Any

import boto3
import numpy as np
import pywt
import torch


class SegmentMapping:
    """Fetches road-segment metadata from DynamoDB with in-memory caching."""

    _CACHE_TTL = 300  # 5 minutes

    def __init__(self, table_name: str, region: str = "ap-southeast-1"):
        self._table_name = table_name
        self._region = region
        self._cache: list[dict[str, Any]] = []
        self._by_index: dict[int, dict[str, Any]] = {}
        self._cache_ts: float = 0

    def _refresh_if_stale(self) -> None:
        if time.time() - self._cache_ts < self._CACHE_TTL and self._cache:
            return
        ddb = boto3.resource("dynamodb", region_name=self._region)
        table = ddb.Table(self._table_name)

        items: list[dict] = []
        resp = table.scan()
        items.extend(resp.get("Items", []))
        while resp.get("LastEvaluatedKey"):
            resp = table.scan(ExclusiveStartKey=resp["LastEvaluatedKey"])
            items.extend(resp.get("Items", []))

        segments = [
            item for item in items if item.get("shape_hash") != "__COUNTER__"
        ]
        self._cache = segments
        self._by_index = {int(s["segment_index"]): s for s in segments}
        self._cache_ts = time.time()

    def get_segment_by_index(self, index: int) -> dict[str, Any] | None:
        self._refresh_if_stale()
        return self._by_index.get(index)

    def get_all_segments(self) -> list[dict[str, Any]]:
        self._refresh_if_stale()
        return sorted(self._cache, key=lambda s: int(s["segment_index"]))

    def get_all_indices(self) -> list[int]:
        self._refresh_if_stale()
        return sorted(self._by_index.keys())

    def get_segment_count(self) -> int:
        self._refresh_if_stale()
        return len(self._cache)

    def get_segment_shape(self, index: int) -> list[dict] | None:
        seg = self.get_segment_by_index(index)
        if seg is None:
            return None
        shape_raw = seg.get("shape", "[]")
        return json.loads(shape_raw) if isinstance(shape_raw, str) else shape_raw


class DataForModel:
    """Preprocess multi-variate speed tensor for TimeXer inference."""

    def __init__(self, data: torch.Tensor):
        self.data = data
        self._preprocess()

    def _preprocess(self) -> None:
        data_np = self.data.numpy() * 3.6

        def dwt_denoise(data: np.ndarray, wavelet: str = "db4", level: int = 1, mode: str = "soft") -> np.ndarray:
            processed = []
            for col in range(data.shape[1]):
                signal = data[:, col]
                coeffs = pywt.wavedec(signal, wavelet, level=level)
                sigma = np.median(np.abs(coeffs[-1])) / 0.6745
                threshold = sigma * np.sqrt(2 * np.log(len(signal)))
                coeffs[1:] = [pywt.threshold(c, threshold, mode=mode) for c in coeffs[1:]]
                denoised = pywt.waverec(coeffs, wavelet)
                processed.append(denoised[: len(signal)])
            return np.column_stack(processed)

        data_np = dwt_denoise(data_np)

        target_width = 325
        if data_np.shape[1] > target_width:
            p = 1
            while p < data_np.shape[1]:
                p *= 2
            target_width = p

        pad_cols = target_width - data_np.shape[1]
        if pad_cols > 0:
            data_np = np.hstack((data_np, np.zeros((data_np.shape[0], pad_cols))))

        self.data = torch.tensor(np.expand_dims(data_np, axis=0), dtype=torch.float32)
        self.num_variates = target_width
