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
        # Lấy danh sách user để ghép tên & SĐT
        res_user = requests.get(
            f"{settings.API_BASE_URL}/api/user-auth/",
            headers=headers,
            timeout=settings.API_TIMEOUT
        )

        if res_taixe.status_code == 200 and res_user.status_code == 200:
            taixe_raw = res_taixe.json()   # [{TaixeID, HinhAnhURL, SoBangLai, ...}]
            users_raw = res_user.json()    # [{UserID, TenDangNhap, SoDienThoai, Vaitro}]

            # Tạo dict user theo UserID để tra cứu nhanh
            user_map = {u['UserID']: u for u in users_raw}

            for tx in taixe_raw:
                tx_id = tx.get('TaixeID', '')
                user_info = user_map.get(tx_id, {})
                taixe_list.append({
                    'id':             tx_id,
                    'ten':            user_info.get('TenDangNhap', tx_id),
                    'soDienThoai':    user_info.get('SoDienThoai', 'Chưa có'),
                    'soBangLai':      tx.get('SoBangLai', ''),
                    'soCCCD':         tx.get('soCCCD', ''),
                    'loaiBangLai':    tx.get('LoaiBangLai', ''),
                    'ngayHetHan':     tx.get('NgayHetHanBangLai', ''),
                    'hinhAnh':        tx.get('HinhAnhURL', ''),
                })
    except requests.exceptions.RequestException:
        pass  # Nếu lỗi kết nối → taixe_list rỗng, template hiển thị trống

    return render(request, 'home/quanlytaixe.html', {'taixe_list': taixe_list})

# ==================== TÀI XẾ (Màn hình của chính Tài Xế) ====================

def taixe(request):
    return render(request, 'home/taixe.html')

def thongtin_taixe(request):
    return render(request, 'home/thongtin_taixe.html')

def taixe_lotrinh(request):
    return render(request, 'home/taixe_lotrinh.html')

def phancongtaixe(request):
    return render(request, 'home/phancongtaixe.html')