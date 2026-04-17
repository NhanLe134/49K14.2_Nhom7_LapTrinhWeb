import requests, json, sys
sys.stdout.reconfigure(encoding='utf-8')

API_BASE = "https://api-vexeapp.onrender.com"
CX_ID = "CX00002"

r = requests.get(f"{API_BASE}/api/chuyenxe/{CX_ID}", timeout=30)
data = r.json()
print(f"Current: {json.dumps(data, ensure_ascii=False)}")

# Try with full Vietnamese
data['TrangThai'] = 'Ch\u01b0a ho\u00e0n th\u00e0nh'
print(f"Trying to set: '{data['TrangThai']}'")
r2 = requests.put(
    f"{API_BASE}/api/chuyenxe/{CX_ID}/",
    json=data,
    headers={"Content-Type": "application/json"},
    timeout=30
)
print(f"Status: {r2.status_code}")
print(f"Response: {r2.text[:300]}")
