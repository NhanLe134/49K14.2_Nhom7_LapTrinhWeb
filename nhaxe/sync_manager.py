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
            # Mapping based on screenshot: LOAIXEID, SOCHO, GIAVE, NGAYCAPNHATGIA
            # Note: Field names might be case-sensitive depending on the API serializer (usually JSON is CamelCase or all lowercase)
            # Normalizing keys to allow both cases just in case
            item = {k.upper(): v for k, v in item.items()}
            
            Loaixe.objects.update_or_create(
                LoaixeID=item.get('LOAIXEID'),
                defaults={
                    'SoCho': item.get('SOCHO', 0),
                    'GiaVe': Decimal(str(item.get('GIAVE', 0))),
                    # NgayCapNhatGia handled by auto_now usually, but we can set if needed
                }
            )
            count += 1
        return count, f"Đã đồng bộ {count} loại xe."

    def sync_xe(self):
        data = self.fetch_data('xe')
        if not data: return 0, "Không thể lấy dữ liệu từ API."
        
        count = 0
        for item in data:
            item = {k.upper(): v for k, v in item.items()}
            
            # Ensure related objects exist or use placeholders
            nhaxe_id = item.get('NHAXEID')
            loaixe_id = item.get('LOAIXEID')
            
            if not nhaxe_id or not loaixe_id: continue
            
            nhaxe_obj, _ = Nhaxe.objects.get_or_create(NhaxeID=nhaxe_id, defaults={'Email': f'{nhaxe_id}@example.com', 'SoDienThoai': '0000000000'})
            loaixe_obj, _ = Loaixe.objects.get_or_create(LoaixeID=loaixe_id, defaults={'SoCho': 0, 'GiaVe': 0})
            
            Xe.objects.update_or_create(
                XeID=item.get('XEID'),
                defaults={
                    'Nhaxe': nhaxe_obj,
                    'Loaixe': loaixe_obj,
                    'BienSoXe': item.get('BIENSOXE', 'N/A'),
                    'TrangThai': item.get('TRANGTHAI', 'Đang hoạt động'),
                }
            )
            count += 1
        return count, f"Đã đồng bộ {count} xe."

    def sync_all(self):
        l_count, _ = self.sync_loaixe()
        x_count, _ = self.sync_xe()
        return l_count + x_count, f"Tổng cộng đã đồng bộ {l_count} loại xe và {x_count} xe."
