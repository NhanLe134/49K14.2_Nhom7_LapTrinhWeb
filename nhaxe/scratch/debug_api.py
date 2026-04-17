import requests

url = "https://api-vexeapp.onrender.com/admin/GETAPI/"
try:
    response = requests.get(url, timeout=10)
    print(f"Status Code: {response.status_code}")
    print(f"Content-Type: {response.headers.get('Content-Type')}")
    print("Content Preview (first 500 chars):")
    print(response.text[:500])
except Exception as e:
    print(f"Error: {e}")
