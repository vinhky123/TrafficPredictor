from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import os

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

class DataGetter(object):
    def __init__(self, client):
        self.client = client

    def get_history_data(self, location):
        collection_name = LOCATIONS.get(location)
        db = self.client["Traffic"]
        collection = db[collection_name]

        results = collection.find({}, {"Speed": 1, "_id": 0}).sort("_id", -1).limit(84)
        speeds = [record["Speed"] for record in results]
        return speeds

    def get_current_data(self, location):
        collection_name = LOCATIONS.get(location)
        db = self.client["Traffic"]
        collection = db[collection_name]

        result = collection.find_one({}, {"Speed": 1, "_id": 0}, sort=[('_id', -1)])
        return result["Speed"]