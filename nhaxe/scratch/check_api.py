import requests
import json

url = "https://api-vexeapp.onrender.com/admin/GETAPI/"
try:
    response = requests.get(url, timeout=10)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        # Print keys or first few items to understand structure
        if isinstance(data, dict):
            print("Keys in response:", data.keys())
            for key, value in data.items():
                if isinstance(value, list):
                    print(f"Table: {key}, count: {len(value)}")
                    if len(value) > 0:
                        print(f"First item in {key}:", value[0])
        elif isinstance(data, list):
            print("Data is a list, count:", len(data))
            if len(data) > 0:
                print("First item:", data[0])
    else:
        print("Error response:", response.text)
except Exception as e:
    print(f"Error connecting: {e}")
