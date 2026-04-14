import requests
from django.conf import settings
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nhom7.settings')
django.setup()

def debug_sync():
    print(f"Base URL: {settings.API_BASE_URL}")
    for ep in ['loaixe', 'xe']:
        url = f"{settings.API_BASE_URL}/api/{ep}/"
        print(f"\nChecking {url}...")
        try:
            resp = requests.get(url, timeout=10)
            print(f"Status: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                print(f"Data count: {len(data)}")
                if data:
                    print("First item keys:", data[0].keys())
                    print("First item sample:", data[0])
            else:
                print(f"Error Response: {resp.text[:500]}")
        except Exception as e:
            print(f"Request Error: {e}")

if __name__ == "__main__":
    debug_sync()
