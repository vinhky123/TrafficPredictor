from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import torch

from ..models.timexer_model import TimeXerModel
from ..repositories.mongo_repository import MongoRepository
from ..utils import DataForModel, SegmentMapping


@dataclass(frozen=True)
class PredictionService:
    repo: MongoRepository
    mapper: SegmentMapping
    model: TimeXerModel

    def update_predictions(self) -> int:
        indices = self.mapper.get_all_indices()
        if not indices:
            return 0

        history_series: list[list[float]] = []
        valid_indices: list[int] = []

        for idx in indices:
            speeds = self.repo.get_recent_speeds(idx, limit=96)
            if not speeds:
                continue
            history_series.append(speeds)
            valid_indices.append(idx)

        if not history_series:
            return 0

        max_len = max(len(s) for s in history_series)
        padded = [s + [0.0] * (max_len - len(s)) for s in history_series]

        # (N, seq_len) -> (seq_len, N)
        data = torch.tensor(padded, dtype=torch.float32).T
        processed = DataForModel(data)
        predict = self.model.predict(processed.data).squeeze(0)

        time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        inserted = 0

        for i, idx in enumerate(valid_indices):
            pred_values = [round(float(v), 2) for v in predict[:, i].tolist()]
            self.repo.insert_prediction(time=time_str, segment_index=idx, speeds=pred_values)
            inserted += 1

        return inserted
