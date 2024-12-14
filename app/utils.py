from mongodb.linker import DBClient

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

        results = collection.find({}, {"Speed": 1, "_id": 0}).sort("_id", -1).limit(84)
        speeds = [record["Speed"] for record in results]
        return speeds

    def get_current_data(self, location):
        collection_name = self.mapper.get_location_name(location)
        db = self.client["Traffic"]
        collection = db[collection_name]

        result = collection.find_one({}, {"Speed": 1, "_id": 0}, sort=[("_id", -1)])
        return result["Speed"]

    def get_predict_data(self, location):
        collection_name = "Predictions"
        db = self.client["Traffic"]
        collection = db[collection_name]
        name = self.mapper.get_location_name(location)

        result = collection.find_one(
            {"Name": name}, {"Speed": 1, "_id": 0}, sort=[("_id", -1)]
        )
        return result["Speed"]
