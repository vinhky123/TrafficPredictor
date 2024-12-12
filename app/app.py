from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
from statistics import mean

from utils.get_data import DataGetter
from mongodb.linker import DBClient

app = Flask(__name__)
CORS(app)

client = DBClient()
getter = DataGetter(client)

@app.route("/current", methods=["POST"])
def predict():

    if not request.is_json:
        return jsonify({"error": "Request payload must be JSON"}), 400

    data = request.get_json()
    data = data.get("location", None)

    if data is None:
        return jsonify({"error": "Request JSON must have 'location' key"}), 400
    
    coordinates = (data["lat"], data["lng"])
    speed_data = getter.get_current_data(coordinates) * 3.6
    speed_data = round(speed_data, 2)

    return jsonify({"Current": speed_data}), 200

    #return jsonify({"result": f"Server ok nha, nhận được {data}"}), 200

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000, debug=False
    )
    #app.run(host="0.0.0.0", port=443, debug=False, ssl_context=("/home/ec2-user/cert.pem", "/home/ec2-user/key.pem"))
