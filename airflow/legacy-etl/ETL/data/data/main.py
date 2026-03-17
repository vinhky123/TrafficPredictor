import os
from dotenv import load_dotenv
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import logging
import datetime
import time
import requests
import json
import boto3
import torch
from utils import (
    filter_roads_data,
    parse_traffic_json,
    map_index_from_coord,
    find_index,
    bot_tele_send_message,
)
from model.model import Model, Config
import numpy as np

checkpoint_path = "./model/checkpoint.pth"

model = Model(Config())
model.eval()
model.load_state_dict(torch.load(checkpoint_path, map_location=torch.device('cpu')))

# Thiết lập logging
logging.basicConfig(
    filename="traffic_etl.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
)
logger = logging.getLogger()


# Load biến môi trường
load_dotenv()
uri = os.getenv("URI")
API_HERE_1 = os.getenv("API_HERE_1")
API_HERE_2 = os.getenv("API_HERE_2")
chat_id = os.getenv("CHAT_ID")
token = os.getenv("BOT_TOKEN")

# Thiết lập MongoClient
client = MongoClient(uri, server_api=ServerApi("1"))
index = client["Traffic"]["IndexRoad"]
traffic = client["Traffic"]["TrafficData"]
INDEX_DICT = map_index_from_coord(index)

# Thiết lập S3
BUCKET_NAME = os.getenv("BUCKET_NAME")
s3_client = boto3.client("s3")

# Cấu hình API
DinhDocLap = (10.777195098260915, 106.69536391705417)
url_here = "https://data.traffic.hereapi.com/v7/flow"
params_here_base = {
    "in": f"circle:{DinhDocLap[0]}, {DinhDocLap[1]};r=20000",
    "locationReferencing": "shape",
}

COUNTER_FILE = "api_counter.txt"
API_CALL_LIMIT = 4850  # Giới hạn lượt gọi cho mỗi API trong một chu kỳ
API1_NAME_IN_FILE = "API_HERE_1"  # Tên dùng để lưu trong file
API2_NAME_IN_FILE = "API_HERE_2"  # Tên dùng để lưu trong file

error_format = "Có lỗi kìa mày, vào check đi. Lỗi là: "


# Hàm chọn API key dựa trên số lần gọi
def get_api_key_and_counter():
    active_api_name = API1_NAME_IN_FILE  # Mặc định ban đầu
    api1_calls = 0
    api2_calls = 0

    # Đọc trạng thái hiện tại từ file
    if os.path.exists(COUNTER_FILE):
        try:
            with open(COUNTER_FILE, "r") as f:
                content = f.read().strip()
                if content:
                    parts = content.split(":")
                    if len(parts) == 3:
                        read_active_api_name, read_api1_calls, read_api2_calls = parts
                        if read_active_api_name in [
                            API1_NAME_IN_FILE,
                            API2_NAME_IN_FILE,
                        ]:
                            active_api_name = read_active_api_name
                            # Chuyển đổi sang int, cẩn thận lỗi ValueError
                            try:
                                api1_calls = int(read_api1_calls)
                                api2_calls = int(read_api2_calls)
                                # Đảm bảo counter không âm
                                api1_calls = max(0, api1_calls)
                                api2_calls = max(0, api2_calls)
                                logger.debug(
                                    f"Read state: {active_api_name}:{api1_calls}:{api2_calls}"
                                )
                            except ValueError:
                                logger.warning(
                                    f"Invalid integer format in counter file: '{content}'. Using default state."
                                )
                                # Reset state if parsing fails
                                active_api_name = API1_NAME_IN_FILE
                                api1_calls = 0
                                api2_calls = 0
                        else:
                            logger.warning(
                                f"Invalid active API name in counter file: {read_active_api_name}. Using default state."
                            )
                    else:
                        logger.warning(
                            f"Invalid format in counter file: '{content}'. Using default state."
                        )
                else:
                    logger.info("Counter file is empty. Using default state.")

        except IOError as e:
            logger.error(f"Error reading counter file: {e}. Using default state.")
        except Exception as e:
            logger.error(
                f"Unexpected error reading counter file: {e}. Using default state."
            )

    # Tăng counter cho API đang active
    current_api_key_object = None
    if active_api_name == API1_NAME_IN_FILE:
        api1_calls += 1
        current_api_key_object = API_HERE_1  # API key dùng cho cuộc gọi này
        current_calls = api1_calls
        current_api_name = API1_NAME_IN_FILE
    else:  # active_api_name == API2_NAME_IN_FILE
        api2_calls += 1
        current_api_key_object = API_HERE_2  # API key dùng cho cuộc gọi này
        current_calls = api2_calls
        current_api_name = API2_NAME_IN_FILE

    # Kiểm tra nếu đạt giới hạn và chuyển API
    if current_calls >= API_CALL_LIMIT:
        if active_api_name == API1_NAME_IN_FILE:
            next_active_api_name = API2_NAME_IN_FILE
            # Reset counter của API vừa hoàn thành chu kỳ
            api1_calls = 0
            message = f"{API1_NAME_IN_FILE} ({API_CALL_LIMIT} calls) reached limit. Switching to {API2_NAME_IN_FILE}. Resetting {API1_NAME_IN_FILE} counter."
        else:  # active_api_name was API2_NAME_IN_FILE
            next_active_api_name = API1_NAME_IN_FILE
            # Reset counter của API vừa hoàn thành chu kỳ
            api2_calls = 0
            message = f"{API2_NAME_IN_FILE} ({API_CALL_LIMIT} calls) reached limit. Switching to {API1_NAME_IN_FILE}. Resetting {API2_NAME_IN_FILE} counter."

        active_api_name = next_active_api_name  # Cập nhật trạng thái active
        # Cập nhật current_api_key_object để trả về key mới sau khi switch
        if active_api_name == API1_NAME_IN_FILE:
            current_api_key_object = API_HERE_1
        else:
            current_api_key_object = API_HERE_2

        logger.info(message)
        # Gửi thông báo Telegram (chỉ khi switch thật sự xảy ra)
        try:
            bot_tele_send_message(message, token, chat_id)
        except Exception as tele_e:
            logger.error(f"Failed to send Telegram notification: {tele_e}")

    # Ghi trạng thái mới nhất vào file
    try:
        with open(COUNTER_FILE, "w") as f:
            f.write(f"{active_api_name}:{api1_calls}:{api2_calls}")
        logger.debug(f"Saved state: {active_api_name}:{api1_calls}:{api2_calls}")
    except IOError as e:
        logger.error(f"Error writing counter file: {e}. API state may be inconsistent.")
    except Exception as e:
        logger.error(
            f"Unexpected error writing counter file: {e}. API state may be inconsistent."
        )

    # Trả về API key object cần dùng cho cuộc gọi này
    # Nó là key sau khi đã xử lý logic switch (nếu có)
    if current_api_key_object is None:
        # Fallback if something went wrong getting the key object
        logger.error(
            "Failed to determine API key object. Using API_HERE_1 as fallback."
        )
        return API_HERE_1
    return current_api_key_object


# Hàm extract
def extract():
    date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        api_key = get_api_key_and_counter()
        params_here = params_here_base.copy()
        params_here["apiKey"] = api_key
        traffic_data = requests.get(url_here, params=params_here).json()
        return True, traffic_data, date
    except Exception as e:
        logger.error(f"Error in extract: {e}")
        bot_tele_send_message(
            error_format + str(e) + " trong phần extract", token, chat_id
        )
        return False, str(e), date


# Hàm filter_roads
def filter_roads(data):
    try:
        if not data[0]:
            return data
        traffic_data = data[1]
        traffic_data_filtered = filter_roads_data(traffic_data, INDEX_DICT)
        return True, traffic_data_filtered, data[2]
    except Exception as e:
        logger.error(f"Error in filter_roads: {e}")
        bot_tele_send_message(
            error_format + str(e) + " trong phần filter", token, chat_id
        )
        return False, str(e), data[2]


# Hàm transform
def transform(data):
    try:
        if not data[0]:
            return data
        traffic_data = data[1]
        traffic_data_transformed = parse_traffic_json(traffic_data)

        if isinstance(traffic_data_transformed, str):
            bot_tele_send_message(
                error_format + traffic_data_transformed, token, chat_id
            )
        return True, traffic_data_transformed, data[2]
    except Exception as e:
        logger.error(f"Error in transform: {e}")
        bot_tele_send_message(
            error_format + str(e) + " trong phần transform", token, chat_id
        )
        return False, str(e), data[2]


# Hàm load
def load(data):
    try:
        if not data[0]:
            return
        date = data[2].replace(" ", "_")  # Thay dấu cách bằng "_"
        traffic_data = data[1]
        final_data = []

        # Lấy tất cả các index từ INDEX_DICT
        all_indices = set(INDEX_DICT.values())

        # Tạo một tập hợp các index đã có trong traffic_data
        available_indices = set()
        for road in traffic_data:
            coord = road["coord"]
            idx = find_index(coord, INDEX_DICT)
            if idx is None:
                logger.warning(f"Invalid or missing index for coord: {coord}")
                continue
            available_indices.add(idx)
            traffic_dict = {"index": idx, "speed": road["speed"], "JF": road["JF"]}
            final_data.append(traffic_dict)

        # Tìm các index còn thiếu
        missing_indices = all_indices - available_indices

        # Nếu có index thiếu, điền bằng giá trị từ một bản ghi bất kỳ hoặc giá trị mặc định
        if missing_indices:
            # Chọn một bản ghi bất kỳ từ traffic_data để sao chép giá trị
            default_road = None
            if traffic_data:
                default_road = traffic_data[0]  # Lấy bản ghi đầu tiên làm mặc định
                default_speed = default_road["speed"]
                default_jf = default_road["JF"]
            else:
                # Nếu traffic_data rỗng, sử dụng giá trị mặc định
                default_speed = 0
                default_jf = 0
                logger.warning("No traffic data available. Using default values (speed=0, JF=0) for missing indices.")

            # Thêm các index thiếu vào final_data
            for idx in missing_indices:
                traffic_dict = {"index": idx, "speed": default_speed, "JF": default_jf}
                final_data.append(traffic_dict)
                logger.info(f"Filled missing index {idx} with speed={default_speed}, JF={default_jf}")

        # Sắp xếp final_data theo index để đảm bảo thứ tự nhất quán
        final_data = sorted(final_data, key=lambda x: x["index"])

        # Ghi dữ liệu vào S3
        file_key = f"TrafficStreaming/real/{date}.json"
        json_data = json.dumps(final_data)
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=file_key,
            Body=json_data,
            ContentType="application/json",
        )
        logger.info(f"Uploaded {len(final_data)} records to S3 at {file_key}")
        return True, None, data[2]
    except Exception as e:
        logger.error(f"Error in load: {e}")
        bot_tele_send_message(
            error_format + str(e) + " trong phần load", token, chat_id
        )
        return False, None, data[2]


# 0.103 0.071 0.088
#Call the ML
def predict(data):
    try:
        if not data[0]:
            logger.warning("No valid data to predict.")
            return

        date = data[2]
        date = datetime.datetime.strptime(date, "%Y-%m-%d %H:%M:%S")

        # List objects in the S3 bucket under the prefix
        prefix = "TrafficStreaming/real/"
        response = s3_client.list_objects_v2(Bucket=BUCKET_NAME, Prefix=prefix)

        if "Contents" not in response:
            logger.error("No objects found in S3 bucket under prefix: {}".format(prefix))
            bot_tele_send_message(
                error_format + "No objects found in S3 bucket for prediction",
                token,
                chat_id
            )
            return

        # Extract and sort objects by timestamp
        objects = []
        for obj in response["Contents"]:
            key = obj["Key"]
            # Extract timestamp from key (remove prefix and .json)
            try:
                timestamp_str = key.replace(prefix, "").replace(".json", "").replace("_", " ")
                obj_date = datetime.datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                if obj_date <= date:  # Only include objects before or at the current timestamp
                    objects.append({"key": key, "timestamp": obj_date})
            except ValueError:
                logger.warning(f"Invalid timestamp format in key: {key}")
                continue

        # Sort objects by timestamp in descending order (most recent first)
        objects = sorted(objects, key=lambda x: x["timestamp"], reverse=True)

        # Select up to 96 most recent objects
        selected_objects = objects[:96]

        if len(selected_objects) < 96:
            logger.warning(
                f"Only {len(selected_objects)} objects found, expected 96. Proceeding with available data."
            )
            bot_tele_send_message(
                f"Warning: Only {len(selected_objects)} objects found for prediction, expected 96.",
                token,
                chat_id
            )

        # Build infer_data from selected objects
        infer_data = []
        for obj in selected_objects:
            file_key = obj["key"]
            try:
                response = s3_client.get_object(Bucket=BUCKET_NAME, Key=file_key)
                decoded_json = response["Body"].read().decode("utf-8")
                data_json = json.loads(decoded_json)
                sorted_data = sorted(data_json, key=lambda x: x["index"])
                speeds = [item["speed"] for item in sorted_data]
                infer_data.append(speeds)
            except Exception as e:
                logger.error(f"Error reading S3 object {file_key}: {e}")
                continue  # Skip problematic objects

        if not infer_data:
            logger.error("No valid data collected for prediction.")
            bot_tele_send_message(
                error_format + "No valid data collected for prediction",
                token,
                chat_id
            )
            return

        # Convert to tensor
        infer_data = torch.tensor(infer_data, dtype=torch.float32)
        infer_data = infer_data.unsqueeze(0)  # Add batch dimension

        # Make prediction
        with torch.no_grad():
            predict_data = model(infer_data, None, None, None)
        predict_data = predict_data.squeeze()

        # Save prediction to S3
        file_key = f"TrafficStreaming/predict/{date.strftime('%Y-%m-%d_%H:%M:%S')}.json"
        predict_dict = {"predict": predict_data.tolist()}
        json_data = json.dumps(predict_dict)
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=file_key,
            Body=json_data,
            ContentType="application/json",
        )
        logger.info(f"Prediction saved to S3 at {file_key}")

    except Exception as e:
        logger.error(f"Error in predict: {e}")
        bot_tele_send_message(
            error_format + str(e) + " trong phần predict", token, chat_id
            )

# Hàm chạy toàn bộ tác vụ
def run_task():
    extracted = extract()
    filtered = filter_roads(extracted)
    transformed = transform(filtered)
    loaded = load(transformed)
    predict(loaded)


# Hàm tính thời gian chạy tiếp theo
def get_next_run_time():
    now = datetime.datetime.now()
    minute = now.minute
    next_minute = ((minute // 5) + 1) * 5
    if next_minute >= 60:
        next_time = (now + datetime.timedelta(hours=1)).replace(
            minute=0, second=0, microsecond=0
        )
    else:
        next_time = now.replace(minute=next_minute, second=0, microsecond=0)
    # Đảm bảo next_time luôn ở tương lai
    while next_time <= now:
        next_time += datetime.timedelta(minutes=5)
    return next_time


# Vòng lặp chính
if __name__ == "__main__":
    current_run = get_next_run_time()
    logger.info(f"Khởi động script, lần chạy đầu tiên: {current_run}")
    while True:
        sleep_seconds = (current_run - datetime.datetime.now()).total_seconds()
        if sleep_seconds > 0:
            time.sleep(sleep_seconds)
        try:
            logger.info(f"Bắt đầu chạy tại: {datetime.datetime.now()}")
            run_task()
        except Exception as e:
            logger.error(f"Error in run_task: {e}")
            bot_tele_send_message(
                error_format + str(e) + " trong run_task", token, chat_id
            )
        current_run += datetime.timedelta(minutes=5)

