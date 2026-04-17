import requests, json, sys
sys.stdout.reconfigure(encoding='utf-8')

API_BASE = "https://api-vexeapp.onrender.com"
CX_ID = "CX45033"

print(f"=== Testing CX_ID: {CX_ID} ===")
r = requests.get(f"{API_BASE}/api/chuyenxe/{CX_ID}", timeout=30)
data = r.json()
print(f"Current TrangThai: {data.get('TrangThai')}")

data['TrangThai'] = 'Hoàn thành'
print(f"Setting TrangThai to: 'Hoàn thành' (len={len(data['TrangThai'])})")

r2 = requests.put(
    f"{API_BASE}/api/chuyenxe/{CX_ID}/",
    json=data,
    headers={"Content-Type": "application/json"},
    timeout=30
)
print(f"PUT Status: {r2.status_code}")
print(f"PUT Response: {r2.text[:300]}")

r3 = requests.get(f"{API_BASE}/api/chuyenxe/{CX_ID}", timeout=30)
print(f"Final TrangThai: {r3.json().get('TrangThai')}")
