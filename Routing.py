# ===========================================
# routing.py
# Hybrid Geocoding (Geoapify) + Routing (ORS)
# ===========================================

import requests
import openrouteservice
import json
import re
import os

# =========================
# 🔑 API Keys
# =========================
GEOAPIFY_API_KEY = "a4a65c593972426b833699a35d9aec01"
ORS_API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjhjMGQ3MWFhODc1MjRhNzJhNjg1YmYxNGI2ZjliNjU2IiwiaCI6Im11cm11cjY0In0="

# =========================
# ⚙️ Clients
# =========================
ors_client = openrouteservice.Client(key=ORS_API_KEY)

# =========================
# 🧩 Address Normalization
# =========================
def normalize_address(address: str) -> str:
    """
    Chuẩn hoá địa chỉ để tăng độ chính xác khi geocoding.
    - Loại bỏ tiền tố, ký tự rác.
    - Viết lại theo cấu trúc chuẩn cho Geoapify.
    """
    main_part = address.split(",")[0].strip()
    number_match = re.match(r"(\d+)", main_part)
    number = number_match.group(1) if number_match else ""

    # Loại bỏ tiền tố “Đ.” hoặc “Đg.” → “Đường”
    street_name = re.sub(r"^\d+[\/\d]*\s*", "", main_part).strip()
    street_name = re.sub(r"^(Đ\.?|Đg\.?)\s*", "", street_name, flags=re.IGNORECASE).strip()

    normalized = f"Hẻm {number} {street_name}, Ho Chi Minh City, Vietnam"
    return normalized.strip()

# =========================
# 📍 Geocode via Geoapify
# =========================
def geocode_address(address: str):
    """
    Lấy toạ độ từ địa chỉ thông qua Geoapify API.
    Trả về (lon, lat)
    """
    normalized = normalize_address(address)
    url = f"https://api.geoapify.com/v1/geocode/search?text={normalized}&apiKey={GEOAPIFY_API_KEY}"

    response = requests.get(url)
    if response.status_code != 200:
        raise ConnectionError(f"Lỗi kết nối Geoapify: {response.status_code}")

    data = response.json()
    features = data.get("features", [])
    if not features:
        raise ValueError(f"Không tìm thấy toạ độ cho địa chỉ: {address}")

    lon = features[0]["geometry"]["coordinates"][0]
    lat = features[0]["geometry"]["coordinates"][1]
    return (lon, lat)

# =========================
# 🛣️ Route Calculation
# =========================
def get_route(user_lat, user_lon, dest_lat, dest_lon):
    """
    Tính đường đi giữa user và điểm đến (ORS Directions API)
    """
    coords = [(user_lon, user_lat), (dest_lon, dest_lat)]
    route = ors_client.directions(
        coordinates=coords,
        profile="driving-car",
        format="geojson"
    )
    return route["features"][0]["geometry"]["coordinates"]

# =========================
# 🧠 Preprocess Restaurants
# =========================
def preprocess_restaurants(user_lat, user_lon):
    """
    Geocode toàn bộ nhà hàng và tính sẵn tuyến đường.
    Lưu ra file restaurants_preprocessed.json
    """
    input_path = "restaurants.json"
    output_path = "restaurants_preprocessed.json"

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Không tìm thấy file {input_path}")

    with open(input_path, "r", encoding="utf-8") as f:
        restaurants = json.load(f)

    for r in restaurants:
        try:
            dest_coords = geocode_address(r["Address"])
            route_coords = get_route(user_lat, user_lon, dest_coords[1], dest_coords[0])

            r["NormalizedAddress"] = normalize_address(r["Address"])
            r["Coordinates"] = dest_coords
            r["Route"] = route_coords

            name = r.get("Name", r.get("Address", "Unknown"))
            print(f"✅ Xử lý: {name}")
        except Exception as e:
            name = r.get("Name", r.get("Address", "Unknown"))
            print(f"⚠️ Lỗi xử lý {name}: {e}")
            continue

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(restaurants, f, ensure_ascii=False, indent=2)

    print(f"💾 Đã lưu dữ liệu vào {output_path}")

# =========================
# 🚀 Get route by index (API dùng)
# =========================
def get_routes_from_json(index: int):
    file_path = "restaurants_preprocessed.json"
    if not os.path.exists(file_path):
        raise FileNotFoundError("File dữ liệu đã preprocess không tồn tại. Hãy chạy preprocess_restaurants() trước.")

    with open(file_path, "r", encoding="utf-8") as f:
        restaurants = json.load(f)

    if index < 0 or index >= len(restaurants):
        raise IndexError("Index không hợp lệ.")

    selected = restaurants[index]

    # 🩵 Đảm bảo có key "Name"
    name = selected.get("Name", selected.get("name", "Không rõ tên"))

    route_data = {
        "name": name,
        "address": selected.get("NormalizedAddress", selected.get("Address", "")),
        "coordinates": selected.get("Coordinates", []),
        "route": selected.get("Route", []),
    }

    return route_data

