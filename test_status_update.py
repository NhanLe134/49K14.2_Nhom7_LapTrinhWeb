import requests, sys
sys.stdout.reconfigure(encoding='utf-8')

API_BASE = "https://api-vexeapp.onrender.com"
CX_ID = "CX48557"

print(f"--- Updating {CX_ID} to 'Hoàn thành' ---")
r_get = requests.get(f"{API_BASE}/api/chuyenxe/{CX_ID}/")
if r_get.status_code != 200:
    print(f"GET Failed: {r_get.status_code}")
    sys.exit(1)

data = r_get.json()
data['TrangThai'] = 'Hoàn thành'
# data['trangThai'] = 'Hoàn thành' # Try both

r_put = requests.put(
    f"{API_BASE}/api/chuyenxe/{CX_ID}/",
    json=data,
    headers={"Content-Type": "application/json"}
)
print(f"PUT Status: {r_put.status_code}")
print(f"PUT Response: {r_put.text}")

r_final = requests.get(f"{API_BASE}/api/chuyenxe/{CX_ID}/")
print(f"Final TrangThai: '{r_final.json().get('TrangThai')}'")
