from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Xe, Loaixe, Nhaxe

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
    import random
    from django.http import JsonResponse
    from .models import Nhaxe

    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('dangnhap')

    nha_xe = Nhaxe.objects.filter(NhaxeID=user_id).first()
    if not nha_xe:
        # Fallback if profile doesn't exist yet (already handled by previous fix but safe here)
        nha_xe = Nhaxe.objects.create(
            NhaxeID=user_id,
            Email=request.session.get('username', 'user') + "@example.com",
            SoDienThoai="0000000000"
        )

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'send_otp':
            otp = str(random.randint(100000, 999999))
            request.session['update_otp'] = otp
            # Simulate sending OTP
            messages.info(request, f"[SIMULATION] Mã xác thực của bạn là: {otp}")
            print(f"DEBUG: OTP for {user_id}: {otp}")
            return JsonResponse({'status': 'sent'})

        elif action == 'save':
            otp_verified = True
            phone = request.POST.get('phone')
            password = request.POST.get('password')
            confirm_password = request.POST.get('confirm_password')

            # Check if verification is needed
            needs_otp = False
            if phone and phone != nha_xe.SoDienThoai:
                needs_otp = True
            if password and password != "*************": # Placeholder from UI
                needs_otp = True

            if needs_otp:
                user_otp = request.POST.get('otp')
                if user_otp != request.session.get('update_otp'):
                    return JsonResponse({'status': 'error', 'message': 'Mã xác thực không chính xác.'})
            
            # Save data
            nha_xe.DiaChiTruSo = request.POST.get('address')
            if phone:
                nha_xe.SoDienThoai = phone
            
            # Image upload
            if 'anh_dai_dien' in request.FILES:
                nha_xe.AnhDaiDien = request.FILES['anh_dai_dien']
            
            nha_xe.save()
            
            # Handle password change (In a real app, this would update the auth service)
            if password and password != "*************":
                # messages.success(request, "Mật khẩu đã được đổi thành công.")
                pass

            return JsonResponse({'status': 'success', 'message': 'Cập nhật thông tin thành công!'})

    return render(request, 'home/thong_tin_nha_xe.html', {'nha_xe': nha_xe})

def quanlytuyenxe(request):
    return render(request, 'home/quanlytuyenxe.html')

def quanly_loaixe(request):
    return render(request, 'home/quanly_loaixe.html')

def quan_ly_xe(request):
    nha_xe_id = request.session.get('user_id')
    if not nha_xe_id:
        return redirect('dangnhap')
    
    # Check if Nhaxe exists locally, create if missing (since we auth via external API)
    nha_xe = Nhaxe.objects.filter(NhaxeID=nha_xe_id).first()
    if not nha_xe:
        username = request.session.get('username', 'User')
        # Create a placeholder record to prevent 404. 
        # In a real app, this should probably redirect to a profile completion page.
        nha_xe = Nhaxe.objects.create(
            NhaxeID=nha_xe_id,
            Email=f"{username.lower().replace(' ', '')}_{nha_xe_id.lower()}@example.com",
            SoDienThoai=f"0{abs(hash(nha_xe_id)) % 1000000000:09d}"
        )
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'delete':
            xe_id = request.POST.get('xe_id')
            Xe.objects.filter(XeID=xe_id, Nhaxe=nha_xe).delete()
            messages.success(request, "Đã xóa xe thành công.")
            return redirect('quan_ly_xe')

        # Xử lý thêm/sửa xe
        bien_so = request.POST.get('bien_so')
        trang_thai = request.POST.get('trang_thai', 'Đang hoạt động')
        so_ghe = request.POST.get('so_ghe')
        loaixe_id = request.POST.get('loaixe_id')
        hinh_anh = request.FILES.get('hinh_anh')
        xe_id = request.POST.get('xe_id')

        # Kiểm tra trùng biển số (tránh lỗi IntegrityError)
        if Xe.objects.filter(BienSoXe=bien_so).exclude(XeID=xe_id).exists():
            messages.error(request, f"Biển số xe '{bien_so}' đã tồn tại trong hệ thống. Vui lòng kiểm tra lại.")
            return redirect('quan_ly_xe')
        
        # Nếu chọn "Thêm loại mới"
        if loaixe_id == 'new':
            ten_loai = request.POST.get('new_loai_ten')
            new_so_cho = request.POST.get('new_loai_socho')
            new_gia = request.POST.get('new_loai_gia')
            
            # Tạo Loaixe mới
            new_loai = Loaixe.objects.create(
                SoCho=new_so_cho,
                GiaVe=new_gia
            )
            # Bạn có thể muốn lưu TenLoaiXe vào CHITIETLOAIXE hoặc một cách khác
            # Ở đây tôi sẽ dùng LoaixeID vừa tạo
            loaixe_obj = new_loai
        else:
            loaixe_obj = get_object_or_404(Loaixe, LoaixeID=loaixe_id)
            
        xe_id = request.POST.get('xe_id')
        if xe_id: # Sửa
            xe = get_object_or_404(Xe, XeID=xe_id, Nhaxe=nha_xe)
            xe.BienSoXe = bien_so
            xe.TrangThai = trang_thai
            xe.SoGhe = so_ghe
            xe.Loaixe = loaixe_obj
            if hinh_anh:
                xe.HinhAnhXe = hinh_anh
            xe.save()
            messages.success(request, "Cập nhật xe thành công.")
        else: # Thêm mới
            Xe.objects.create(
                Nhaxe=nha_xe,
                Loaixe=loaixe_obj,
                BienSoXe=bien_so,
                TrangThai=trang_thai,
                SoGhe=so_ghe,
                HinhAnhXe=hinh_anh
            )
            messages.success(request, "Thêm xe mới thành công.")
            
        return redirect('quan_ly_xe')

    # GET request
    vehicles = Xe.objects.filter(Nhaxe=nha_xe).select_related('Loaixe')
    
    # Lấy danh sách loại xe kèm tên hãng (nếu có) từ bảng CHITIETLOAIXE
    from .models import CHITIETLOAIXE
    vehicle_types = CHITIETLOAIXE.objects.filter(Nhaxe=nha_xe).select_related('Loaixe')
    
    return render(request, 'home/quan_ly_xe.html', {
        'vehicles': vehicles,
        'vehicle_types': vehicle_types
    })

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