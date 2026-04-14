from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
import requests

# ==================== NHÀ XE (Quản lý Tài Xế) ====================

def quanlytaixe(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('index')

    headers = {'Authorization': f"Bearer {request.session.get('token', '')}"}
    taixe_list = []

    try:
        # Lấy danh sách tài xế
        res_taixe = requests.get(
            f"{settings.API_BASE_URL}/api/taixe/",
            headers=headers,
            timeout=settings.API_TIMEOUT
        )
        if res_taixe.status_code == 200:
            taixe_raw = res_taixe.json()   # [{TaixeID, HinhAnhURL, SoBangLai, ...}]

            for tx in taixe_raw:
                tx_id = tx.get('TaixeID', '')
                taixe_list.append({
                    'id':             tx_id,
                    'ten':            tx_id, # Không có tên, dùng ID làm định danh
                    'soDienThoai':    'N/A',
                    'soBangLai':      tx.get('SoBangLai', ''),
                    'soCCCD':         tx.get('soCCCD', ''),
                    'loaiBangLai':    tx.get('LoaiBangLai', ''),
                    'ngayHetHan':     tx.get('NgayHetHanBangLai', ''),
                    'hinhAnh':        tx.get('HinhAnhURL', ''),
                })
    except requests.exceptions.RequestException:
        pass  # Nếu lỗi kết nối → taixe_list rỗng, template hiển thị trống

    return render(request, 'home/quanlytaixe.html', {'taixe_list': taixe_list})

def them_tai_xe(request):
    if request.method == 'POST':
        cccd = request.POST.get('cccd', '')
        so_bang_lai = request.POST.get('license', '')
        loai_bang_lai = request.POST.get('licenseType', '')
        ngay_het_han = request.POST.get('licenseExpiry', '')
        
        try:
            # Lấy list để gen ID mới (TAIxxxx)
            res_list = requests.get(f"{settings.API_BASE_URL}/api/taixe/")
            new_id = "TAI0001"
            if res_list.status_code == 200:
                data = res_list.json()
                if data:
                    max_id = max([int(d.get('TaixeID', 'TAI0000').replace('TAI', '')) for d in data])
                    new_id = f"TAI{max_id + 1:04d}"

            tx_payload = {
                "TaixeID": new_id,
                "HinhAnhURL": "",
                "SoBangLai": so_bang_lai,
                "soCCCD": cccd,
                "LoaiBangLai": loai_bang_lai,
                "NgayHetHanBangLai": ngay_het_han
            }
            res_tx = requests.post(f"{settings.API_BASE_URL}/api/taixe/", json=tx_payload)
            if res_tx.status_code in [200, 201]:
                messages.success(request, f'Thêm tài xế {new_id} thành công')
            else:
                messages.error(request, 'Lỗi hệ thống lập tài xế. Vui lòng thử lại sau.')
        except requests.exceptions.RequestException:
             messages.error(request, 'Lỗi kết nối. Vui lòng thử lại sau.')
             
    return redirect('quanlytaixe')

def sua_tai_xe(request, pk):
    if request.method == 'POST':
        so_bang_lai = request.POST.get('license', '')
        loai_bang_lai = request.POST.get('licenseType', '')
        ngay_het_han = request.POST.get('licenseExpiry', '')
        
        try:
            tx_payload = {
                "SoBangLai": so_bang_lai,
                "LoaiBangLai": loai_bang_lai,
                "NgayHetHanBangLai": ngay_het_han
            }
            res_tx = requests.patch(f"{settings.API_BASE_URL}/api/taixe/{pk}/", json=tx_payload)
            # Dùng PUT nếu server chỉ có simple viewset
            if res_tx.status_code not in [200, 204]:
                res_tx = requests.put(f"{settings.API_BASE_URL}/api/taixe/{pk}/", json=tx_payload)
            
            if res_tx.status_code in [200, 204]:
                messages.success(request, 'Cập nhật thông tin thành công')
            else:
                messages.error(request, 'Lỗi hệ thống lập tài xế. Vui lòng thử lại sau.')
        except requests.exceptions.RequestException:
            messages.error(request, 'Lỗi hệ thống. Vui lòng thử lại sau.')
            
    return redirect('quanlytaixe')

def xoa_tai_xe(request, pk):
    if request.method == 'POST':
        try:
            # Check conditions (phân công / chuyến xe) if needed from /api/phancong/
            # ... simple delete for now based on spec doesn't require checking active trips for Driver deletion
            # Delete from taixe
            res_tx = requests.delete(f"{settings.API_BASE_URL}/api/taixe/{pk}/")
            if res_tx.status_code in [200, 204]:
                 messages.success(request, 'Xóa tài xế thành công.')
            else:
                 messages.error(request, 'Lỗi hệ thống. Vui lòng thử lại sau.')
        except requests.exceptions.RequestException:
             messages.error(request, 'Lỗi hệ thống. Vui lòng thử lại sau.')
    return redirect('quanlytaixe')

# ==================== TÀI XẾ (Màn hình của chính Tài Xế) ====================

def taixe(request):
    return render(request, 'home/taixe.html')

def thongtin_taixe(request):
    return render(request, 'home/thongtin_taixe.html')

def taixe_lotrinh(request):
    return render(request, 'home/taixe_lotrinh.html')

def phancongtaixe(request):
    return render(request, 'home/phancongtaixe.html')