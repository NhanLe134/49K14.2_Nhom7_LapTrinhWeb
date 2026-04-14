from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
import requests
from django.conf import settings
import random

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
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('dangnhap')

    headers = {'Authorization': f"Bearer {request.session.get('token', '')}"}
    api_url = f"{settings.API_BASE_URL}/api/nhaxe/{user_id}/"
    
    nha_xe_data = {}
    try:
        response = requests.get(api_url, headers=headers, timeout=settings.API_TIMEOUT)
        if response.status_code == 200:
            nha_xe_data = response.json()
        else:
            # Nếu chưa có profile trên API, dùng dữ liệu session làm mặc định
            nha_xe_data = {
                'NhaxeID': user_id,
                'Email': request.session.get('username', 'user') + "@example.com",
                'SoDienThoai': 'Chưa có',
                'DiaChiTruSo': 'Chưa cập nhật'
            }
    except Exception:
        messages.error(request, 'Không thể kết nối tới máy chủ API để lấy thông tin.')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'send_otp':
            otp = str(random.randint(100000, 999999))
            request.session['update_otp'] = otp
            messages.info(request, f"[SIMULATION] Mã xác thực của bạn là: {otp}")
            return JsonResponse({'status': 'sent'})

        elif action == 'save':
            phone = request.POST.get('phone')
            password = request.POST.get('password')
            
            # Validation OTP
            needs_otp = False
            if phone and phone != nha_xe_data.get('SoDienThoai'):
                needs_otp = True
            
            if needs_otp:
                user_otp = request.POST.get('otp')
                if user_otp != request.session.get('update_otp'):
                    return JsonResponse({'status': 'error', 'message': 'Mã xác thực không chính xác.'})
            
            # Chuẩn bị payload gửi lên API
            payload = {
                'NhaxeID': user_id,
                'DiaChiTruSo': request.POST.get('address'),
                'SoDienThoai': phone if phone else nha_xe_data.get('SoDienThoai'),
            }
            
            try:
                # Gửi yêu cầu cập nhật (PUT hoặc POST tùy API)
                res_update = requests.put(api_url, json=payload, headers=headers, timeout=settings.API_TIMEOUT)
                if res_update.status_code in [200, 204]:
                    return JsonResponse({'status': 'success', 'message': 'Cập nhật thông tin thành công!'})
                else:
                    return JsonResponse({'status': 'error', 'message': f'Lỗi API ({res_update.status_code}).'})
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': f'Lỗi kết nối: {str(e)}'})

    return render(request, 'home/thong_tin_nha_xe.html', {'nha_xe': nha_xe_data})

def quanlytuyenxe(request):
    return render(request, 'home/quanlytuyenxe.html')

def quanly_loaixe(request):
    nha_xe_id = request.session.get('user_id')
    headers = {'Authorization': f"Bearer {request.session.get('token', '')}"}
    loaixe_list = []
    try:
        res = requests.get(f"{settings.API_BASE_URL}/api/loaixe/", headers=headers, timeout=settings.API_TIMEOUT)
        if res.status_code == 200:
            raw_data = res.json()
            for item in raw_data:
                loaixe_list.append({
                    'LoaiXeId': item.get('LoaixeID'),
                    'TenLoaiXe': f"Loại xe {item.get('SoCho')} chỗ",
                    'SoGhe': item.get('SoCho'),
                    'GiaVe': item.get('GiaVe'),
                    'NgayCapNhat': item.get('NgayCapNhatGia')
                })
    except Exception:
        messages.error(request, "Lỗi kết nối API lấy danh sách loại xe.")
        
    return render(request, 'home/quanly_loaixe.html', {'loaixe_list': loaixe_list})

def cap_nhat_gia_ve(request, pk):
    if request.method == 'POST':
        headers = {'Authorization': f"Bearer {request.session.get('token', '')}"}
        new_price = request.POST.get('gia_ve')
        payload = {"GiaVe": new_price}
        try:
            res = requests.put(f"{settings.API_BASE_URL}/api/loaixe/{pk}/", json=payload, headers=headers, timeout=settings.API_TIMEOUT)
            if res.status_code in [200, 204]:
                messages.success(request, "Cập nhật giá vé thành công.")
            else:
                messages.error(request, "Cập nhật giá vé thất bại trên server.")
        except Exception:
            messages.error(request, "Lỗi kết nối API.")
            
    return redirect('quanly_loaixe')


def quan_ly_xe(request):
    from .sync_manager import SyncManager
    nha_xe_id = request.session.get('user_id')
    if not nha_xe_id:
        return redirect('dangnhap')
    
    headers = {'Authorization': f"Bearer {request.session.get('token', '')}"}
    api_url_xe = f"{settings.API_BASE_URL}/api/xe/"
    api_url_loaixe = f"{settings.API_BASE_URL}/api/loaixe/"
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'delete':
            xe_id = request.POST.get('xe_id')
            try:
                res = requests.delete(f"{api_url_xe}{xe_id}/", headers=headers, timeout=settings.API_TIMEOUT)
                if res.status_code in [200, 204]:
                    messages.success(request, "Đã xóa xe thành công.")
                else:
                    messages.error(request, f"Lỗi xóa xe (API: {res.status_code}).")
            except Exception as e:
                messages.error(request, f"Lỗi kết nối: {str(e)}")
            return redirect('quan_ly_xe')

        # Xử lý thêm/sửa xe
        bien_so = request.POST.get('bien_so')
        trang_thai = request.POST.get('trang_thai', 'Đang hoạt động')
        so_ghe = request.POST.get('so_ghe')
        loaixe_id = request.POST.get('loaixe_id')
        xe_id = request.POST.get('xe_id')

        # Nếu chọn "Thêm loại mới"
        if loaixe_id == 'new':
            ten_loai = request.POST.get('new_loai_ten')
            new_so_cho = request.POST.get('new_loai_socho')
            new_gia = request.POST.get('new_loai_gia')
            
            # Tạo Loaixe mới via API
            try:
                loai_payload = {"SoCho": new_so_cho, "GiaVe": new_gia}
                res_loai = requests.post(api_url_loaixe, json=loai_payload, headers=headers, timeout=settings.API_TIMEOUT)
                if res_loai.status_code in [200, 201]:
                    loaixe_id = res_loai.json().get('LoaixeID')
                else:
                    messages.error(request, "Lỗi tạo loại xe mới.")
                    return redirect('quan_ly_xe')
            except Exception:
                messages.error(request, "Lỗi kết nối tạo loại xe.")
                return redirect('quan_ly_xe')

        # Payload cho xe
        xe_payload = {
            "nhaXeId": nha_xe_id,
            "loaixeId": loaixe_id,
            "bienSoXe": bien_so,
            "trangThai": trang_thai,
            "soGhe": so_ghe
        }
        
        try:
            if xe_id: # Sửa
                res = requests.put(f"{api_url_xe}{xe_id}/", json=xe_payload, headers=headers, timeout=settings.API_TIMEOUT)
                msg = "Cập nhật xe thành công."
            else: # Thêm mới
                res = requests.post(api_url_xe, json=xe_payload, headers=headers, timeout=settings.API_TIMEOUT)
                msg = "Thêm xe mới thành công."
                
            if res.status_code in [200, 201, 204]:
                messages.success(request, msg)
            else:
                messages.error(request, f"Thao tác thất bại (API: {res.status_code}).")
        except Exception as e:
            messages.error(request, f"Lỗi kết nối: {str(e)}")
            
        return redirect('quan_ly_xe')

    # GET request
    vehicles = []
    vehicle_types = []
    try:
        # Lấy danh sách xe và lọc
        res_xe = requests.get(api_url_xe, headers=headers, timeout=settings.API_TIMEOUT)
        if res_xe.status_code == 200:
            all_xe = res_xe.json()
            # Lọc xe thuộc nhà xe này (giả định API trả về nhaXeId hoặc nhaXe object)
            vehicles = [x for x in all_xe if str(x.get('nhaXeId') or x.get('nhaXe')).strip() == str(nha_xe_id)]
            
        # Lấy danh sách loại xe
        res_loai = requests.get(api_url_loaixe, headers=headers, timeout=settings.API_TIMEOUT)
        if res_loai.status_code == 200:
            vehicle_types = res_loai.json()
    except Exception:
        messages.error(request, "Lỗi kết nối API Server.")
    
    return render(request, 'home/quan_ly_xe.html', {
        'vehicles': vehicles,
        'vehicle_types': vehicle_types
    })


def quanlytaixe(request):
    return render(request, 'home/quanlytaixe.html')

def quanly_khachhang(request):
    user_id = request.session.get('user_id')
    headers = {'Authorization': f"Bearer {request.session.get('token', '')}"}
    khach_hang_data = {}
    try:
        res = requests.get(f"{settings.API_BASE_URL}/api/user-auth/{user_id}/", headers=headers, timeout=settings.API_TIMEOUT)
        if res.status_code == 200:
            khach_hang_data = res.json()
    except Exception:
        pass
    return render(request, 'home/quanly_khachhang.html', {'khach_hang': khach_hang_data})

def quanlyve(request):
    user_id = request.session.get('user_id')
    headers = {'Authorization': f"Bearer {request.session.get('token', '')}"}
    ve_list = []
    try:
        res = requests.get(f"{settings.API_BASE_URL}/api/ve/", headers=headers, timeout=settings.API_TIMEOUT)
        if res.status_code == 200:
            all_ve = res.json()
            # Lọc vé của khách hàng này
            ve_list = [v for v in all_ve if str(v.get('KhachHangID') or v.get('khachHangId')).strip() == str(user_id)]
    except Exception:
        messages.error(request, "Lỗi kết nối API lấy danh sách vé.")
        
    return render(request, 'home/quanlyve.html', {'ve_list': ve_list})

# ==================== TÀI XẾ (tx) ====================

def taixe(request):
    return render(request, 'home/taixe.html')

def thongtin_taixe(request):
    return render(request, 'home/thongtin_taixe.html')


def taixe_lotrinh(request):
    return render(request, 'home/taixe_lotrinh.html')

def phancongtaixe(request):
    return render(request, 'home/phancongtaixe.html')