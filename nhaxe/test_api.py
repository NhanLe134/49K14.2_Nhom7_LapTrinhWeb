import requests

def get_mapped_location(location_name):
    location_name_lower = location_name.strip().lower()
    if location_name_lower == "huế":
        return "FH7V+7Q Thuận Hóa, Huế, Việt Nam"
    elif location_name_lower == "đà nẵng":
        return "36CJ+H3 An Hải, Đà Nẵng, Việt Nam"
    elif location_name_lower == "hội an":
        return "V8GG+7MR, An Hội, Hội An, Đà Nẵng, Việt Nam"
    return location_name

def get_distance_from_google_maps(origin, destination, waypoints=None):
    api_key = "AIzaSyA6gA4Miz-VvAkBwkKSD0E698xvd4IgmWc"
    
    origin_mapped = get_mapped_location(origin)
    destination_mapped = get_mapped_location(destination)
    
    # Sử dụng Distance Matrix API thay cho Directions API
    url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    params = {
        "origins": origin_mapped,
        "destinations": destination_mapped,
        "key": api_key
    }
    
    # Distance Matrix API ko hỗ trợ waypoints tốt như Directions API,
    # nhưng ta có thể tạm dùng để xem key có bị khóa Distance Matrix không
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        print("Status (Distance Matrix):", data['status'])
        if data['status'] == 'OK' and data['rows'][0]['elements'][0]['status'] == 'OK':
            distance_meters = data['rows'][0]['elements'][0]['distance']['value']
            return round(distance_meters / 1000.0, 1)
        else:
            print("Error:", data.get('error_message'))
    except Exception as e:
        print("Exception:", e)
    return None

if __name__ == "__main__":
    print(get_distance_from_google_maps("Huế", "Đà Nẵng"))
