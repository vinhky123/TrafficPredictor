import requests
from pyspark.sql.types import (
    StructType,
    StructField,
    DoubleType,
    ArrayType,
    StringType,
    IntegerType,
)
from pyspark.sql import Row, SparkSession, DataFrame
import datetime


def map_index_from_coord(collection, spark):
    all_indices = list(collection.find({}, {"_id": 0, "coord.coordinates": 1, "id": 1}))
    index_dict = {
        tuple(map(tuple, doc["coord"]["coordinates"])): doc["id"] for doc in all_indices
    }

    index_data = [
        Row(points=[Row(lat=p[1], lng=p[0]) for p in coord_tuple], index=idx)
        for coord_tuple, idx in index_dict.items()
    ]

    index_schema = StructType(
        [
            StructField(
                "points",
                ArrayType(
                    StructType(
                        [
                            StructField("lat", DoubleType(), True),
                            StructField("lng", DoubleType(), True),
                        ]
                    )
                ),
                True,
            ),
            StructField("index", IntegerType(), True),
        ]
    )

    index_df = spark.createDataFrame(index_data, schema=index_schema)
    return index_df


def find_index(coord, INDEX_DICT):
    coord_tuple = tuple(map(tuple, coord))
    return INDEX_DICT.get(coord_tuple)


def reverse_coord_list(coord):
    return [[lng, lat] for lat, lng in coord]


def send_message_discord(web_hook, message):
    content = {"content": message}
    try:
        requests.post(web_hook, json=content)
        print("Tin nhắn đã được gửi qua Discord!")
    except Exception as e:
        print(f"Không gửi được tin nhắn Discord: {e}")


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


if __name__ == "__main__":
    ...

