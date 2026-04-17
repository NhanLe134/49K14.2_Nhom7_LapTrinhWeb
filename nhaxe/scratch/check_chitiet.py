import requests
import os
import django

# Setup django environment to get settings
import sys
sys.path.append('d:/PycharmProjects/49K14.2_Nhom7_LapTrinhWeb')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nhom7.settings')
django.setup()

from django.conf import settings

url = f"{settings.API_BASE_URL}/api/chitiittaixe/"
try:
    response = requests.get(url, timeout=10)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print("Data Sample:")
        if isinstance(data, list) and len(data) > 0:
            print(data[0])
        else:
            print(data)
    else:
        print(response.text[:500])
except Exception as e:
    print(f"Error: {e}")
