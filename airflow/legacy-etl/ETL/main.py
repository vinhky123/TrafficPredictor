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
from decimal import Decimal

from pyspark.sql.functions import col, lit, when
from pyspark.sql.types import *
from pyspark.sql.functions import col, explode, struct, array, lit, collect_list

from pyspark.sql import SparkSession

from typing import Dict, Set, Tuple

from utils import (
    map_index_from_coord,
    find_index,
    send_message_discord,
    get_next_run_time,
)


# Thiết lập logging
logging.basicConfig(
    filename="traffic_etl.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
)
logger = logging.getLogger()


spark = (
    SparkSession.builder.appName("TrafficETL")
    .master("local[*]")
    .getOrCreate()
    .sparkContext
)

# Load biến môi trường
load_dotenv()
uri = os.getenv("URI")
API_HERE_1 = os.getenv("API_HERE_1")
API_HERE_2 = os.getenv("API_HERE_2")
chat_id = os.getenv("CHAT_ID")
token = os.getenv("BOT_TOKEN")
webhook = os.getenv("WEBHOOK")
DYNAMODB_TABLE = os.getenv("DYNAMODB_TABLE")

# Thiết lập MongoClient
client = MongoClient(uri, server_api=ServerApi("1"))
index = client["Traffic"]["IndexRoad"]
traffic = client["Traffic"]["TrafficData"]
INDEX_DICT = map_index_from_coord(index, spark)


# Cấu hình API
DinhDocLap = (10.777195098260915, 106.69536391705417)
url_here = "https://data.traffic.hereapi.com/v7/flow"
params_here_base = {
    "in": f"circle:{DinhDocLap[0]}, {DinhDocLap[1]};r=20000",
    "locationReferencing": "shape",
}

# Cấu hình dynamodb
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(DYNAMODB_TABLE)

COUNTER_FILE = "api_counter.txt"
API_CALL_LIMIT = 4850  # Giới hạn lượt gọi cho mỗi API trong một chu kỳ
API1_NAME_IN_FILE = "API_HERE_1"  # Tên dùng để lưu trong file
API2_NAME_IN_FILE = "API_HERE_2"  # Tên dùng để lưu trong file

error_format = "@everyone Có lỗi kìa mày, vào check đi. Lỗi là: "


def get_api_key_and_counter():
    active_api_name = API1_NAME_IN_FILE  # Mặc định ban đầu
    api1_calls = 0
    api2_calls = 0

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
        if active_api_name == API1_NAME_IN_FILE:
            current_api_key_object = API_HERE_1
        else:
            current_api_key_object = API_HERE_2

        logger.info(message)
        try:
            send_message_discord(webhook, message)
        except Exception as tele_e:
            logger.error(f"Failed to send Telegram notification: {tele_e}")

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

    if current_api_key_object is None:
        # Fallback if something went wrong getting the key object
        logger.error(
            "Failed to determine API key object. Using API_HERE_1 as fallback."
        )
        return API_HERE_1
    return current_api_key_object


schema = StructType(
    [
        StructField("sourceUpdated", StringType(), True),
        StructField(
            "results",
            ArrayType(
                StructType(
                    [
                        StructField(
                            "location",
                            StructType(
                                [
                                    StructField("description", StringType(), True),
                                    StructField("length", DoubleType(), True),
                                    StructField(
                                        "shape",
                                        StructType(
                                            [
                                                StructField(
                                                    "links",
                                                    ArrayType(
                                                        StructType(
                                                            [
                                                                StructField(
                                                                    "points",
                                                                    ArrayType(
                                                                        StructType(
                                                                            [
                                                                                StructField(
                                                                                    "lat",
                                                                                    DoubleType(),
                                                                                    True,
                                                                                ),
                                                                                StructField(
                                                                                    "lng",
                                                                                    DoubleType(),
                                                                                    True,
                                                                                ),
                                                                            ]
                                                                        )
                                                                    ),
                                                                    True,
                                                                ),
                                                                StructField(
                                                                    "length",
                                                                    DoubleType(),
                                                                    True,
                                                                ),
                                                            ]
                                                        )
                                                    ),
                                                    True,
                                                )
                                            ]
                                        ),
                                        True,
                                    ),
                                ]
                            ),
                            True,
                        ),
                        StructField(
                            "currentFlow",
                            StructType(
                                [
                                    StructField("speed", DoubleType(), True),
                                    StructField("speedUncapped", DoubleType(), True),
                                    StructField("freeFlow", DoubleType(), True),
                                    StructField("jamFactor", DoubleType(), True),
                                    StructField("confidence", DoubleType(), True),
                                    StructField("traversability", StringType(), True),
                                ]
                            ),
                            True,
                        ),
                    ]
                )
            ),
            True,
        ),
    ]
)


# Hàm extract
def extract():
    date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        api_key = get_api_key_and_counter()
        params_here = params_here_base.copy()
        params_here["apiKey"] = api_key
        traffic_data = requests.get(url_here, params=params_here).json()
        df = spark.read.json(
            spark.sparkContext.parallelize([traffic_data]), schema=schema
        )

        return True, df, date
    except Exception as e:
        logger.error(f"Error in extract: {e}")
        send_message_discord(
            web_hook=webhook, message=error_format + str(e) + " trong phần extract"
        )
        return False, str(e), date


# Hàm transform
def transform(data):
    try:
        if not data[0]:
            return data
        df = data[1]
        date = data[2]

        filtered_df = (
            df.select(explode("results").alias("result"))
            .select("result.location.shape.links", "result.currentFlow")
            .select(explode("links").alias("link"), "currentFlow")
            .select(
                col("link.points").alias("points"),
                col("currentFlow.speed").alias("speed"),
            )
        )

        transformed_df = filtered_df.join(
            INDEX_DICT, filtered_df["points"] == INDEX_DICT["points"], "inner"
        ).select(lit(date).alias("date"), col("index"), col("speed"))

        if isinstance(transformed_df, str):
            send_message_discord(
                web_hook=webhook, message=error_format + transformed_df
            )
        return True, transformed_df, data[2]

    except Exception as e:
        logger.error(f"Error in transform: {e}")
        send_message_discord(
            web_hook=webhook, message=error_format + str(e) + " trong phần transform"
        )
        return False, str(e), data[2]


# Hàm load
def load(data):
    try:
        if not data[0]:
            return
        traffic_data = data[1]

        if traffic_data.rdd.isEmpty():
            logger.info(
                "Transformed DataFrame is empty. Nothing to load into DynamoDB."
            )
            return

        def save_partition_to_dynamodb(partition):

            with table.batch_writer() as batch:
                for row in partition:
                    if (
                        row.index is not None
                        and row.date is not None
                        and row.speed is not None
                    ):
                        item = {
                            "index": int(row.index),
                            "date": row.date,
                            "speed": Decimal(str(row.speed)),
                        }
                        batch.put_item(Item=item)

        traffic_data.rdd.foreachPartition(save_partition_to_dynamodb)

    except Exception as e:
        logger.error(f"Error in load: {e}")
        send_message_discord(
            web_hook=webhook, message=error_format + str(e) + " trong phần load"
        )


# Hàm chạy toàn bộ tác vụ
def run_task():
    extracted = extract()
    transformed = transform(extracted)
    load(transformed)


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
            send_message_discord(
                web_hook=webhook, message=error_format + str(e) + " trong run task"
            )
        current_run += datetime.timedelta(minutes=5)

