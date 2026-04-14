from django.shortcuts import render, redirect
from django.contrib import messages
import requests
from django.conf import settings
from datetime import datetime

# Các hàm đăng nhập / đăng xuất đã được chuyển sang auth_views.py

# ==================== TRANG CHUNG ====================

def timkiem(request):
    return render(request, 'home/timkiem.html')

def quen_mat_khau(request):
    return render(request, 'home/quen_mat_khau.html')

def dangky_khachhang(request):
    return render(request, 'home/dangky_khachhang.html')

def dangky_nhaxe(request):
    return render(request, 'home/dangky_nhaxe.html')

# ==================== KHÁCH HÀNG (kh) ====================

def khachhang(request):
    return render(request, 'home/khachhang.html')

def thongtin_khachhang(request):
    return render(request, 'home/thongtin_khachhang.html')

def lotrinh(request):
    return render(request, 'home/lotrinh.html')

def chitietchuyenxe(request):
    return render(request, 'home/chitietchuyenxe.html')

def vecuatoi(request):
    return render(request, 'home/vecuatoi.html')

def vietdanhgia(request):
    return render(request, 'home/vietdanhgia.html')

def dadanhgia(request):
    return render(request, 'home/dadanhgia.html')

def danhgiachuyenxe(request):
    return render(request, 'home/danhgiachuyenxe.html')

# ==================== NHÀ XE (nx) ====================

def nhaxe(request):
    return render(request, 'home/nhaxe.html')

def thong_tin_nha_xe(request):
    return render(request, 'home/thong_tin_nha_xe.html')

def quanlytuyenxe(request):
    # Lấy nha_xe_id từ session, mặc định là NX00001 nếu chưa đăng nhập/không tìm thấy
    nha_xe_id = request.session.get('nha_xe_id', 'NX00001')
    return render(request, 'home/quanlytuyenxe.html', {'nha_xe_id': nha_xe_id})

def quanly_loaixe(request):
    # Danh sách 3 loại xe mặc định theo yêu cầu thiết kế
    loaixe_mặc_định = [
        {'LoaiXeId': 'LX00001', 'TenLoaiXe': 'Loại xe A', 'SoGhe': '4', 'GiaVe': None, 'NgayCapNhat': None},
        {'LoaiXeId': 'LX00002', 'TenLoaiXe': 'Loại xe B', 'SoGhe': '7', 'GiaVe': None, 'NgayCapNhat': None},
        {'LoaiXeId': 'LX00003', 'TenLoaiXe': 'Loại xe C', 'SoGhe': '9', 'GiaVe': None, 'NgayCapNhat': None}
    ]

    api_url = f"{settings.API_BASE_URL}/api/loaixe"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    
    try:
        response = requests.get(api_url, headers=headers, timeout=settings.API_TIMEOUT)
        if response.status_code == 200:
            try:
                api_data = response.json()
                if isinstance(api_data, list):
                    for xe_api in api_data:
                        # Lấy dữ liệu thực tế từ JSON của Postman
                        api_id = xe_api.get('LoaixeID')
                        api_so_cho = xe_api.get('SoCho')
                        api_gia_ve = xe_api.get('GiaVe')
                        api_ngay_cap_nhat = xe_api.get('NgayCapNhatGia')
                        
                        for xe_macdinh in loaixe_mặc_định:
                            # Ghép dữ liệu dựa trên số chỗ ngồi (4, 7, 9)
                            if str(api_so_cho) == str(xe_macdinh['SoGhe']):
                                xe_macdinh['LoaiXeId'] = api_id # Lưu lại ID thật (VD: LX00002)
                                xe_macdinh['GiaVe'] = api_gia_ve
                                xe_macdinh['NgayCapNhat'] = api_ngay_cap_nhat
            except ValueError:
                pass
    except Exception as e:
        print(f"GET error: {e}")

    return render(request, 'home/quanly_loaixe.html', {'loaixe_list': loaixe_mặc_định})

def capnhat_gia_loaixe(request, loaixe_id):
    if request.method == 'POST':
        gia_moi = request.POST.get('gia_ve')
        
        # Thử gọi API Cập nhật theo URL ban đầu của bạn
        api_url = f"{settings.API_BASE_URL}/admin/PUTAPI/loaixe/{loaixe_id}/"

        # Payload sửa lại theo đúng tên biến của API
        data = {
            "GiaVe": str(gia_moi), # API của bạn trả về string "130000" nên gửi string cho an toàn
            "NgayCapNhatGia": datetime.now().strftime("%Y-%m-%d") # Format yyyy-mm-dd
        }
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        try:
            response = requests.put(api_url, json=data, headers=headers, timeout=settings.API_TIMEOUT)
            
            if response.status_code in [200, 204]:
                messages.success(request, "Cập nhật giá vé thành công!")
            elif response.status_code == 404:
                messages.error(request, f"Lỗi 404: Không tìm thấy loại xe có ID là {loaixe_id}.")
            elif response.status_code in [401, 403]:
                messages.error(request, "Lỗi 403: Máy chủ từ chối quyền cập nhật. Cần có Token bảo mật.")
            else:
                messages.error(request, f"Lỗi {response.status_code}: Không thể cập nhật giá vé.")
        except Exception as e:
            messages.error(request, "Lỗi kết nối đến máy chủ khi cập nhật giá vé.")

    return redirect('quanly_loaixe')

def quan_ly_xe(request):
    return render(request, 'home/quan_ly_xe.html')

def quanlytaixe(request):
    return render(request, 'home/quanlytaixe.html')

def quanly_khachhang(request):
    return render(request, 'home/quanly_khachhang.html')

def quanlyve(request):
    return render(request, 'home/quanlyve.html')

# ==================== TÀI XẾ (tx) ====================

def taixe(request):
    return render(request, 'home/taixe.html')

def thongtin_taixe(request):
    return render(request, 'home/thongtin_taixe.html')

def taixe_lotrinh(request):
    return render(request, 'home/taixe_lotrinh.html')

def phancongtaixe(request):
    return render(request, 'home/phancongtaixe.html')
