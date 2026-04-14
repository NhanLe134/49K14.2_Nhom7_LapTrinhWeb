import requests
from django.conf import settings
from .models import Loaixe, Xe, Nhaxe, TuyenXe, Taixe
from decimal import Decimal

class SyncManager:
    def __init__(self, token=None):
        self.base_url = settings.API_BASE_URL
        self.headers = {}
        if token:
            self.headers['Authorization'] = f"Bearer {token}"
    
    def fetch_data(self, endpoint):
        url = f"{self.base_url}/api/{endpoint}/"
        try:
            response = requests.get(url, headers=self.headers, timeout=settings.API_TIMEOUT)
            if response.status_code == 200:
                return response.json()
            return None
        except requests.exceptions.RequestException:
            return None

    def sync_loaixe(self):
        data = self.fetch_data('loaixe')
        if not data: return 0, "Không thể lấy dữ liệu từ API hoặc API trống."
        
        count = 0
        for item in data:
            # API: LoaixeID, SoCho, GiaVe
            Loaixe.objects.update_or_create(
                LoaixeID=item.get('LoaixeID'),
                defaults={
                    'SoCho': item.get('SoCho', 0),
                    'GiaVe': Decimal(str(item.get('GiaVe', 0))),
                }
            )
            count += 1
        return count, f"Đã đồng bộ {count} loại xe."

    def sync_xe(self, forced_nhaxe=None):
        data = self.fetch_data('xe')
        if not data: return 0, "Không thể lấy dữ liệu từ API."
        
        count = 0
        for item in data:
            # API: XeID, TrangThai, SoGhe, BienSoXe, Nhaxe, Loaixe
            xe_id = item.get('XeID')
            nhaxe_id = item.get('Nhaxe')
            loaixe_id = item.get('Loaixe')
            
            if not nhaxe_id or not loaixe_id: continue
            
            # If forced_nhaxe is provided (e.g. from current session), use it.
            # Otherwise, find or create the one from the API data.
            if forced_nhaxe:
                nhaxe_obj = forced_nhaxe
            else:
                nhaxe_obj, _ = Nhaxe.objects.get_or_create(
                    NhaxeID=nhaxe_id, 
                    defaults={'Email': f'{nhaxe_id}@example.com', 'SoDienThoai': '0000000000'}
                )
            
            loaixe_obj, _ = Loaixe.objects.get_or_create(
                LoaixeID=loaixe_id, 
                defaults={'SoCho': 0, 'GiaVe': 0}
            )
            
            Xe.objects.update_or_create(
                XeID=xe_id,
                defaults={
                    'Nhaxe': nhaxe_obj,
                    'Loaixe': loaixe_obj,
                    'BienSoXe': item.get('BienSoXe') or 'N/A',
                    'TrangThai': item.get('TrangThai') or 'Đang hoạt động',
                    'SoGhe': item.get('SoGhe') or 0,
                }
            )
            count += 1
        return count, f"Đã đồng bộ {count} xe."

    def push_nhaxe(self, nhaxe_obj):
        """Ensure the Nhaxe exists on the API."""
        url = f"{self.base_url}/api/nhaxe/"
        payload = {
            "NhaxeID": nhaxe_obj.NhaxeID,
            "TenNhaxe": getattr(nhaxe_obj, 'TenNhaxe', nhaxe_obj.NhaxeID),
            "Email": nhaxe_obj.Email,
            "SoDienThoai": nhaxe_obj.SoDienThoai,
        }
        try:
            # Try to POST (create)
            requests.post(url, json=payload, headers=self.headers, timeout=settings.API_TIMEOUT)
            # If 400 (already exists), we ignore or PUT. For now, just ensuring existence is enough.
            return True
        except:
            return False

    def push_xe(self, xe_obj):
        # 1. Ensure Nhaxe exists on API first
        self.push_nhaxe(xe_obj.Nhaxe)

        # 2. Push local vehicle to API
        url = f"{self.base_url}/api/xe/"
        payload = {
            'XeID': xe_obj.XeID,
            'BienSoXe': xe_obj.BienSoXe,
            'TrangThai': xe_obj.TrangThai or 'Đang hoạt động',
            'SoGhe': int(xe_obj.SoGhe or 0),
            'Nhaxe': xe_obj.Nhaxe.NhaxeID,
            'Loaixe': xe_obj.Loaixe.LoaixeID,
        }
        try:
            # Try POST first
            response = requests.post(url, json=payload, headers=self.headers, timeout=settings.API_TIMEOUT)
            if response.status_code in [200, 201]:
                return True, "Đã đồng bộ lên API thành công."
            
            # If failed, try PUT to the detail endpoint
            put_url = f"{url}{xe_obj.XeID}/"
            response = requests.put(put_url, json=payload, headers=self.headers, timeout=settings.API_TIMEOUT)
            if response.status_code in [200, 204]:
                return True, "Đã cập nhật lên API thành công."
                
            return False, f"Lỗi API: {response.text[:100]}"
        except Exception as e:
            return False, str(e)

    def sync_all(self, forced_nhaxe=None):
        """Batch sync everything."""
        l_count, _ = self.sync_loaixe()
        x_count, _ = self.sync_xe(forced_nhaxe=forced_nhaxe)
        return l_count + x_count, f"Tổng cộng đã đồng bộ {l_count} loại xe và {x_count} xe."
