from __future__ import annotations

from dataclasses import dataclass

import torch

from .model import GetModel


@dataclass(frozen=True)
class TimeXerModel:
    model: GetModel

    @staticmethod
    def from_path(model_path: str) -> "TimeXerModel":
        return TimeXerModel(model=GetModel(model_state_path=model_path))

    def predict(self, data: torch.Tensor) -> torch.Tensor:
        return self.model.predict(data)

