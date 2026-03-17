import requests


def map_index_from_coord(collection):
    all_indices = list(collection.find({}, {"_id": 0, "coord.coordinates": 1, "id": 1}))
    index_dict = {
        tuple(map(tuple, doc["coord"]["coordinates"])): doc["id"] for doc in all_indices
    }
    return index_dict


def find_index(coord, INDEX_DICT):
    coord_tuple = tuple(map(tuple, coord))
    return INDEX_DICT.get(coord_tuple)


def reverse_coord_list(coord):
    return [[lng, lat] for lat, lng in coord]


def filter_roads_data(data, INDEX_DICT):
    selected_coords = set(INDEX_DICT.keys())
    selected = []  # Danh sách giữ lại
    results = data.get("results", [])

    for result in results:
        coord = []

        links = result.get("location", {}).get("shape", {}).get("links", [])
        for link in links:
            points = link.get("points", [])
            if not points:
                continue

            for point in points:
                lat = point.get("lat", 0)
                lng = point.get("lng", 0)
                coord.append((lat, lng))

            if coord:  # Chỉ xử lý khi có dữ liệu
                coord_tuple = tuple(map(tuple, reverse_coord_list(coord)))

                if coord_tuple in selected_coords:
                    selected.append(result)
                    break

    return selected


def parse_traffic_json(data):
    traffic_data = []

    for result in data:
        name = result.get("location", {}).get("description", "Unknown")
        coord = []

        links = result.get("location", {}).get("shape", {}).get("links", [])
        for link in links:
            points = link.get("points", [])
            for point in points:
                lat = point.get("lat", 0)
                lng = point.get("lng", 0)
                coord.append([lng, lat])

        speed = result.get("currentFlow", {}).get("speed", 0)
        JF = result.get("currentFlow", {}).get("jamFactor", 0)

        traffic_data.append(
            {
                "name": name,
                "coord": coord,
                "speed": speed,
                "JF": JF,
            }
        )

    return traffic_data


def bot_tele_send_message(message, token, chat_id):
    url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={message}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        print("Tin nhắn đã được gửi qua Telegram!")
    except Exception as e:
        print(f"Không gửi được tin nhắn Telegram: {e}")

