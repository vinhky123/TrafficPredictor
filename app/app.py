from flask import Flask, request, jsonify
from flask_cors import CORS
from app.models.model import GetModel
from utils import DataGetter, Mapping
from mongodb.linker import DBClient
import torch
import time

app = Flask(__name__)
CORS(app)

client = DBClient()
data_getter = DataGetter(client)
model = GetModel()
mapper = Mapping()


#####################################################################################################
@app.route("/", methods=["GET"])
def home():
    return (
        """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Home</title>
    </head>
    <body>
        <h1>Welcome to the Traffic Prediction App</h1>
        <p>Vào /current endpoint để lấy thông tin</p>
        <p>Vào <a href="https://traffic-predictor-one.vercel.app/">ĐÂY</a> để sử dụng</p>
    </body>
    </html>
    """,
        200,
    )


#####################################################################################################
@app.route("/db_notice", methods=["POST"])
def get_notice():
    if not request.is_json:
        return jsonify({"error": "Request payload must be JSON"}), 400

    data = request.get_json()

    if data.get("notice") == "update":
        coordinates = mapper.get_all_location()
        data = list()
        for coordinate in coordinates:
            history_data = data_getter.get_history_data(coordinate)
            data.append(history_data)
        data = torch.tensor(data, dtype=torch.float32)
        predict = model.predict(data.T)
        predict = predict.squeeze(0).tolist()  # [1, 12, 10] -> [12, 10]

        return jsonify({"notice": "Updating DB and predicting"}), 200
    else:
        return jsonify({"error": "Invalid request"}), 400


#####################################################################################################
@app.route("/current", methods=["POST"])
def current():

    if not request.is_json:
        return jsonify({"error": "Request payload must be JSON"}), 400

    data = request.get_json()
    data = data.get("location", None)

    if data is None:
        return jsonify({"error": "Request JSON must have 'location' key"}), 400

    coordinates = (data["lat"], data["lng"])
    speed_data = data_getter.get_current_data(coordinates) * 3.6
    speed_data = round(speed_data, 2)

    return jsonify({"Current": speed_data}), 200


#####################################################################################################
@app.route("/predict", methods=["POST"])
def predict():
    if not request.is_json:
        return jsonify({"error": "Request payload must be JSON"}), 400

    data = request.get_json()
    data = data.get("location", None)

    if data is None:
        return jsonify({"error": "Request JSON must have 'location' key"}), 400

    coordinates = (data["lat"], data["lng"])
    speed_data = data_getter.get_history_data(coordinates)
    predict_speed = model.predict(speed_data)

    return jsonify({"Predict": predict_speed}), 200


#####################################################################################################
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
