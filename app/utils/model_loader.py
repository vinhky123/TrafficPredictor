import os
import torch
from models.Model import TimeXer

def load_model():
    model_path = os.path.join(os.path.dirname(__file__), '..', 'models', 'TimeXer.pth')
    model = TimeXer(
        seq_len=108,
        patch_len=12,
        patch_num=108 // 12,
        num_variate=162,
        pred_len=12,
        d_model=256,
        num_layers=4
    )
    state_dict = torch.load(model_path, map_location=torch.device('cpu'), weights_only=True)
    model.load_state_dict(state_dict)

    return model