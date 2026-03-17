from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import torch

from ..repositories.mongo_repository import MongoRepository
from ..utils import DataForModel, Mapping
from ..models.timexer_model import TimeXerModel


@dataclass(frozen=True)
class PredictionService:
    repo: MongoRepository
    mapper: Mapping
    model: TimeXerModel

    def update_predictions(self) -> int:
        coordinates = self.mapper.get_all_location()
        history_series = []
        for coordinate in coordinates:
            location_name = self.mapper.get_location_name(coordinate)
            if not location_name:
                history_series.append([])
                continue
            speeds = self.repo.get_recent_speeds(location_name, limit=96)
            history_series.append(speeds)

        data = torch.tensor(history_series, dtype=torch.float32).T
        data = DataForModel(data).data

        predict = self.model.predict(data).squeeze(0)
        time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        inserted = 0
        for i, coordinate in enumerate(coordinates):
            name = self.mapper.get_location_name(coordinate)
            if not name:
                continue
            predict_i = [round(float(speed), 2) for speed in predict[:, i].tolist()]
            self.repo.insert_prediction(time=time_str, name=str(name), speeds=predict_i)
            inserted += 1

        return inserted

