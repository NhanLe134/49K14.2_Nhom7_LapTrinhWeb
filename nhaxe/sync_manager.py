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

    def sync_xe(self):
        data = self.fetch_data('xe')
        if not data: return 0, "Không thể lấy dữ liệu từ API."
        
        count = 0
        for item in data:
            # API: XeID, TrangThai, SoGhe, BienSoXe, Nhaxe, Loaixe
            xe_id = item.get('XeID')
            nhaxe_id = item.get('Nhaxe')
            loaixe_id = item.get('Loaixe')
            
            if not nhaxe_id or not loaixe_id: continue
            
            # Ensure related objects exist
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

    def push_xe(self, xe_obj):
        # Push local vehicle to API
        url = f"{self.base_url}/api/xe/"
        payload = {
            'XeID': xe_obj.XeID,
            'BienSoXe': xe_obj.BienSoXe,
            'TrangThai': xe_obj.TrangThai,
            'SoGhe': xe_obj.SoGhe or 0,
            'Nhaxe': xe_obj.Nhaxe.NhaxeID,
            'Loaixe': xe_obj.Loaixe.LoaixeID,
        }
        try:
            # We use POST to create or update if the API supports it (usually REST)
            # If the ID exists, DRF usually expects PUT/PATCH at /{id}/
            # For simplicity, we try POST first.
            response = requests.post(url, json=payload, headers=self.headers, timeout=settings.API_TIMEOUT)
            if response.status_code in [200, 201]:
                return True, "Đã đồng bộ lên API thành công."
            elif response.status_code == 400: # Maybe ID already exists, try PUT
                put_url = f"{url}{xe_obj.XeID}/"
                response = requests.put(put_url, json=payload, headers=self.headers, timeout=settings.API_TIMEOUT)
                if response.status_code == 200:
                    return True, "Đã cập nhật lên API thành công."
            return False, f"Lỗi API: {response.text[:100]}"
        except Exception as e:
            return False, str(e)

    def sync_tuyenxe(self):
        data = self.fetch_data('tuyenxe')
        if not data: return 0, "Không thể lấy dữ liệu Tuyến xe từ API."
        
        count = 0
        for item in data:
            # API: tuyenXeID, tenTuyen, diemDi, diemDen, QuangDuong, DiemTrungGian, nhaXe
            t_id = item.get('tuyenXeID')
            nhaxe_id = item.get('nhaXe')
            if not t_id or not nhaxe_id: continue
            
            nhaxe_obj, _ = Nhaxe.objects.get_or_create(NhaxeID=nhaxe_id, defaults={'Email': f'{nhaxe_id}@example.com', 'SoDienThoai': '0000000000'})
            
            TuyenXe.objects.update_or_create(
                tuyenXeID=t_id,
                defaults={
                    'nhaXe': nhaxe_obj,
                    'tenTuyen': item.get('tenTuyen') or f"{item.get('diemDi')} - {item.get('diemDen')}",
                    'diemDi': item.get('diemDi') or 'Đà Nẵng',
                    'diemDen': item.get('diemDen') or 'Huế',
                    'QuangDuong': item.get('QuangDuong'),
                    'DiemTrungGian': item.get('DiemTrungGian'),
                }
            )
            count += 1
        return count, f"Đã đồng bộ {count} tuyến xe."

    def push_tuyenxe(self, tx_obj):
        url = f"{self.base_url}/api/tuyenxe/"
        payload = {
            'tuyenXeID': tx_obj.tuyenXeID,
            'tenTuyen': tx_obj.tenTuyen,
            'diemDi': tx_obj.diemDi,
            'diemDen': tx_obj.diemDen,
            'QuangDuong': tx_obj.QuangDuong,
            'DiemTrungGian': tx_obj.DiemTrungGian,
            'nhaXe': tx_obj.nhaXe.NhaxeID,
        }
        try:
            response = requests.post(url, json=payload, headers=self.headers, timeout=settings.API_TIMEOUT)
            if response.status_code in [200, 201]:
                return True, "Đã đồng bộ Tuyến xe lên API thành công."
            elif response.status_code == 400:
                put_url = f"{url}{tx_obj.tuyenXeID}/"
                response = requests.put(put_url, json=payload, headers=self.headers, timeout=settings.API_TIMEOUT)
                if response.status_code == 200:
                    return True, "Đã cập nhật Tuyến xe lên API thành công."
            return False, f"Lỗi API Tuyến xe: {response.text[:100]}"
        except Exception as e:
            return False, str(e)

    def sync_all(self):
        l_count, _ = self.sync_loaixe()
        x_count, _ = self.sync_xe()
        t_count, _ = self.sync_tuyenxe()
        return l_count + x_count + t_count, f"Đã đồng bộ {l_count} loại xe, {x_count} xe và {t_count} tuyến xe."
