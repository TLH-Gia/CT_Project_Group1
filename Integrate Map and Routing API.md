# Sub-problem: Integrate Map and Routing API
**Git Branch:** `24127408`  
**Responsible:** Nguyễn Lê Hoàng Khải  
**Project:** *Restaurant Recommend System (Gemini + Map API)*  

---

## I. Objective
Design and implement a **system that suggests optimal routes** to restaurants.  

**Main requirement:**  
- Help users find the **best route to a selected restaurant**.

---

## II. Sub-problem Analysis

| Component | Description | Expected Output |
|-----------|-------------|----------------|
| **1. Input Address Processing** | Increase accuracy by standardizing the address format. | Address formatted for OpenRouteService. |
| **2. User GPS Location** | Dynamically update the user's location on the map. | Show user movement in real time. |
| **3. Geocoding** | Convert addresses into numerical coordinates for routing. | Latitude and longitude values. |
| **4. Route Caching** | Store restaurant routes for faster map rendering. | `restaurants_preprocessed.json` for temporary storage. |
| **5. Map Visualization** | Display starting point, route, and destination. | Interactive map rendered on the web. |

---

## III. Proposed Technologies

| Component | Tool / Library | Notes |
|-----------|----------------|-------|
| **Routing** | OpenRouteService | Compute optimal driving routes. |
| **Map Display** | Leaflet.js + HTML + CSS + JavaScript | Render interactive map. |
| **GPS** | HTML5 Geolocation API | Track current user location dynamically. |
| **Geocoding** | Geoapify | Convert address to coordinates for routing. |
| **Processing Input** | Regex | Format input into address formatted for OpenRouteService.

---

## IV. Data Structures and Code Samples

### 1. Input Address Normalization
```python
def normalize_address(address: str) -> str:
    main_part = address.split(",")[0].strip()
    number_match = re.match(r"(\d+)", main_part)
    number = number_match.group(1) if number_match else ""

    street_name = re.sub(r"^\d+[\/\d]*\s*", "", main_part).strip()
    street_name = re.sub(r"^(Đ\.?|Đg\.?)\s*", "", street_name, flags=re.IGNORECASE).strip()

    normalized = f"Hẻm {number} {street_name}, Ho Chi Minh City, Vietnam"
    return normalized.strip()
```

### 2. Dynamic User Location (GPS)
```python
let watchId = navigator.geolocation.watchPosition(
    (position) => {
        const userLat = position.coords.latitude;
        const userLon = position.coords.longitude;
        console.log("Vị trí hiện tại:", userLat, userLon);

        if (userMarker) {
            userMarker.setLatLng([userLat, userLon]);
        } else {
            userMarker = L.marker([userLat, userLon], {title: "Bạn đang ở đây"}).addTo(map);
        }
    },
    (error) => {
        console.error("Lỗi lấy vị trí:", error);
    },
    {
        enableHighAccuracy: true,
        maximumAge: 10000, // cache 10 giây
        timeout: 5000
    }
);
```

### 3. Geocoding Addresses
```python
def geocode_address(address: str):
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
```

### 4. Preprocessing and Caching Routes
```python
def preprocess_restaurants(user_lat, user_lon):
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
```

### 5. Map Display
```js
let map = L.map('map').setView([10.762622, 106.660172], 13);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom: 19
}).addTo(map);
```

## V. Technology Comparison

| Criterion | Google Places | OpenRouteService | Geoapify |
|-----------|---------------|-----------------|----------|
| **Request limits** | Moderate | Very high | Moderate |
| **Ease of implementation** | Difficult | Very easy | Easy |
| **Accuracy** | Very high | Good | Good |
| **Risk** | High | Low | Low |
| **Project suitability** | Not necessary | Highly suitable | Suitable |

 >**Conclusion:** Choose OpenRouteService because it meets all project requirements, is easy to implement, and provides ample daily requests. Besides, use Geoapify for more accurate geocoding.