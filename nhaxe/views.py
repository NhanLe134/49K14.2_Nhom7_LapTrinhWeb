from datetime import datetime
import random
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.conf import settings
from .models import (
    Nhaxe, Loaixe, Xe, KhachHang, Ve, User_Authentication,
    CHITIETLOAIXE
)

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

    try:
        # Lấy thông tin nhà xe từ Database
        nha_xe_obj = get_object_or_404(Nhaxe, NhaxeID=user_id)
        
        if request.method == 'POST':
            action = request.POST.get('action')

            if action == 'send_otp':
                otp = str(random.randint(100000, 999999))
                request.session['update_otp'] = otp
                messages.info(request, f"[SIMULATION] Mã xác thực của bạn là: {otp}")
                return JsonResponse({'status': 'sent'})

            elif action == 'save':
                phone = request.POST.get('phone')
                address = request.POST.get('address')
                
                # Check OTP if phone changed
                if phone and phone != nha_xe_obj.SoDienThoai:
                    user_otp = request.POST.get('otp')
                    if user_otp != request.session.get('update_otp'):
                        return JsonResponse({'status': 'error', 'message': 'Mã xác thực không chính xác.'})
                
                # Cập nhật trực tiếp vào DB
                nha_xe_obj.SoDienThoai = phone if phone else nha_xe_obj.SoDienThoai
                nha_xe_obj.DiaChiTruSo = address if address else nha_xe_obj.DiaChiTruSo
                nha_xe_obj.save()
                
                return JsonResponse({'status': 'success', 'message': 'Cập nhật thông tin thành công!'})
        
        return render(request, 'home/thong_tin_nha_xe.html', {'nha_xe': nha_xe_obj})
    except Exception as e:
        messages.error(request, f'Lỗi hệ thống: {str(e)}')
        return redirect('nhaxe')

def quanly_loaixe(request):
    try:
        # Mặc định lấy dữ liệu từ DB (Bảng Loaixe)
        loaixe_db = Loaixe.objects.all().order_by('SoCho')
        
        # Nếu DB trống, khởi tạo dữ liệu mẫu (hoặc hiển thị danh sách trống)
        loaixe_list = []
        for lx in loaixe_db:
            loaixe_list.append({
                'LoaiXeId': lx.LoaixeID,
                'SoGhe': str(lx.SoCho),
                'GiaVe': lx.GiaVe,
                'NgayCapNhat': lx.NgayCapNhatGia,
                'TenLoaiXe': f"Loại {lx.SoCho} chỗ"
            })
            
        return render(request, 'home/quanly_loaixe.html', {'loaixe_list': loaixe_list})
    except Exception as e:
        messages.error(request, f"Lỗi DB: {str(e)}")
        return render(request, 'home/quanly_loaixe.html', {'loaixe_list': []})

def capnhat_gia_loaixe(request, loaixe_id):
    if request.method == 'POST':
        gia_moi = request.POST.get('gia_ve')
        try:
            Loaixe.objects.filter(LoaixeID=loaixe_id).update(GiaVe=gia_moi)
            messages.success(request, "Cập nhật giá vé thành công!")
        except Exception as e:
            messages.error(request, f"Lỗi cập nhật: {str(e)}")
    return redirect('quanly_loaixe')

def quan_ly_xe(request):
    nha_xe_id = request.session.get('user_id')
    if not nha_xe_id:
        return redirect('dangnhap')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'delete':
            xe_id = request.POST.get('xe_id')
            try:
                Xe.objects.filter(XeID=xe_id, Nhaxe_id=nha_xe_id).delete()
                messages.success(request, "Đã xóa xe thành công.")
            except Exception as e:
                messages.error(request, f"Lỗi: {str(e)}")
            return redirect('quan_ly_xe')

        # Thêm/Sửa
        bien_so = request.POST.get('bien_so')
        trang_thai = request.POST.get('trang_thai', 'Đang hoạt động')
        so_ghe = request.POST.get('so_ghe')
        loaixe_id = request.POST.get('loaixe_id')
        xe_id = request.POST.get('xe_id')

        try:
            if xe_id: # Sửa
                Xe.objects.filter(XeID=xe_id).update(
                    BienSoXe=bien_so,
                    TrangThai=trang_thai,
                    SoGhe=so_ghe,
                    Loaixe_id=loaixe_id
                )
                messages.success(request, "Cập nhật xe thành công.")
            else: # Thêm mới
                Xe.objects.create(
                    Nhaxe_id=nha_xe_id,
                    BienSoXe=bien_so,
                    TrangThai=trang_thai,
                    SoGhe=so_ghe,
                    Loaixe_id=loaixe_id
                )
                messages.success(request, "Thêm xe mới thành công.")
        except Exception as e:
            messages.error(request, f"Lỗi: {str(e)}")
            
        return redirect('quan_ly_xe')

    # GET
    vehicles = Xe.objects.filter(Nhaxe_id=nha_xe_id)
    vehicle_types = Loaixe.objects.all()
    
    return render(request, 'home/quan_ly_xe.html', {
        'vehicles': vehicles,
        'vehicle_types': vehicle_types
    })

def quanly_khachhang(request):
    user_id = request.session.get('user_id')
    try:
        khach_hang_data = User_Authentication.objects.filter(UserID=user_id).first()
        return render(request, 'home/quanly_khachhang.html', {'khach_hang': khach_hang_data})
    except:
        return render(request, 'home/quanly_khachhang.html', {'khach_hang': None})

def quanlyve(request):
    user_id = request.session.get('user_id')
    try:
        # Lấy vé của khách hàng
        ve_list = Ve.objects.filter(KhachHang_id=user_id).order_by('-NgayDat')
        return render(request, 'home/quanlyve.html', {'ve_list': ve_list})
    except Exception as e:
        messages.error(request, f"Lỗi lấy danh sách vé: {str(e)}")
        return render(request, 'home/quanlyve.html', {'ve_list': []})

# ==================== TÀI XẾ (tx) ====================

def taixe(request):
    return render(request, 'home/taixe.html')

def thongtin_taixe(request):
    return render(request, 'home/thongtin_taixe.html')

def taixe_lotrinh(request):
    return render(request, 'home/taixe_lotrinh.html')

def phancongtaixe(request):
    return render(request, 'home/phancongtaixe.html')
