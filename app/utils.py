from mongodb.linker import DBClient
import pandas as pd
from sklearn.impute import KNNImputer
import pywt
import numpy as np
import torch

LOCATIONS = {
    (10.798905, 106.726998): "SaiGonBride",
    (10.849319, 106.773959): "TD_Crossroads",
    (10.813187, 106.756803): "RachChiec_Bridge",
    (10.793411, 106.700390): "DBP_Bridge",
    (10.772122, 106.657589): "BKU",
    (10.801761, 106.664923): "HoangVanThu_Park",
    (10.777923, 106.681344): "DanChu_Roundabout",
    (10.785456, 106.663261): "LeThiRieng_Park",
    (10.816761, 106.631952): "TruongChinh_Street",
    (10.801900, 106.648617): "CongHoa_Street",
}

NAME = [
    "SaiGonBride",
    "TD_Crossroads",
    "RachChiec_Bridge",
    "DBP_Bridge",
    "BKU",
    "HoangVanThu_Park",
    "DanChu_Roundabout",
    "LeThiRieng_Park",
    "TruongChinh_Street",
    "CongHoa_Street",
]


class Mapping:
    def __init__(self):
        pass

    def get_location_name(self, location):
        return LOCATIONS.get(location)

    def get_location_index(self, location):
        return NAME.index(LOCATIONS.get(location)) + 1

    def get_all_location(self):
        return list(LOCATIONS.keys())


class DataGetter(object):
    def __init__(self, client):
        self.mapper = Mapping()
        self.client = client

    def get_history_data(self, location):
        collection_name = self.mapper.get_location_name(location)
        db = self.client["Traffic"]
        collection = db[collection_name]

        results = collection.find({}, {"Speed": 1, "_id": 0}).sort("_id", -1).limit(96)
        speeds = [record["Speed"] for record in results]
        return speeds

    def get_current_data(self, location):
        collection_name = self.mapper.get_location_name(location)
        db = self.client["Traffic"]
        collection = db[collection_name]

        result = collection.find_one({}, {"Speed": 1, "_id": 0}, sort=[("_id", -1)])
        return result["Speed"]

    def get_all_data(self):
        locations = self.mapper.get_all_location()
        db = self.client["Traffic"]

        data = {}

        for location in locations:
            location_name = self.mapper.get_location_name(location)
            collection = db[location_name]

            results = collection.find({}, {"Speed": 1, "_id": 0}).sort("_id", -1)
            speeds = [
                (
                    round(record.get("Speed", 0) * 3.6, 2)
                    if record.get("Speed") is not None
                    else 0
                )
                for record in results
            ]
            data[location_name] = speeds

        df = pd.DataFrame(data)

        df.to_csv("traffic_data.csv", index=False)

        return df

    def get_predict_data(self, location):
        collection_name = "Predictions"
        db = self.client["Traffic"]
        collection = db[collection_name]
        name = self.mapper.get_location_name(location)

        result = collection.find_one(
            {"Name": name}, {"Speed": 1, "_id": 0}, sort=[("_id", -1)]
        )
        return result["Speed"]


class DataForModel(object):
    def __init__(self, data):
        self.data = data
        self.preprocessing()

    def preprocessing(self):
        data_np = self.data.numpy() * 3.6
        data_np = np.delete(data_np, [1, -1], axis=1)

        def DWT_preprocess_tensor(data, wavelet="db4", level=1, thresholding="soft"):
            processed_data = []
            for col in range(data.shape[1]):
                signal = data[:, col]
                coeffs = pywt.wavedec(signal, wavelet, level=level)

                sigma = np.median(np.abs(coeffs[-1])) / 0.6745
                threshold = sigma * np.sqrt(2 * np.log(len(signal)))
                coeffs[1:] = [
                    pywt.threshold(c, threshold, mode=thresholding) for c in coeffs[1:]
                ]

                denoised_signal = pywt.waverec(coeffs, wavelet)
                processed_data.append(denoised_signal[: len(signal)])

            return np.column_stack(processed_data)

        data_np = DWT_preprocess_tensor(data_np)

        num_cols_to_add = 325 - data_np.shape[1]
        if num_cols_to_add > 0:
            zero_cols = np.zeros((data_np.shape[0], num_cols_to_add))
            data_np = np.hstack((data_np, zero_cols))

        data_np = np.expand_dims(data_np, axis=0)

        self.data = torch.tensor(data_np, dtype=torch.float32)
