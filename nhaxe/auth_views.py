from datetime import datetime
import random
import json
import time
import re
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.conf import settings
from django.db import transaction
from .models import User_Authentication, KhachHang, Nhaxe, Loaixe, CHITIETLOAIXE

# ==================== ĐĂNG NHẬP / ĐĂNG XUẤT ====================

def index(request):
    """Trang đăng nhập - nếu đã login thì redirect thẳng vào trang tương ứng."""
    if request.session.get('user_id'):
        role = request.session.get('role', '')
        return _redirect_by_role(role)
    return render(request, 'home/index.html')


def dangnhap(request):
    """
    View xử lý đăng nhập:
    - Kiểm tra trống trường.
    - Đếm số lần sai để khóa tài khoản (5 lần).
    """
    if request.method == 'GET':
        if request.session.get('user_id'):
            role = request.session.get('role', '')
            return _redirect_by_role(role)
        return render(request, 'home/index.html')

    # Xử lý POST
    username = request.POST.get('username', '').strip()
    password = request.POST.get('password', '')
    
    # 1. Kiểm tra khóa tài khoản
    failed_count = request.session.get('failed_login_count', 0)
    if failed_count >= 5:
        return render(request, 'home/index.html', {
            'username_value': username,
            'is_locked': True,
            'error_general': 'Bạn đã nhập sai mật khẩu trên 5 lần. Tài khoản của bạn đã bị khóa.'
        })

    # 2. Kiểm tra bỏ trống
    errors = {}
    if not username:
        errors['username'] = 'Vui lòng nhập tên đăng nhập'
    if not password:
        errors['password'] = 'Vui lòng nhập mật khẩu'
    
    if errors:
        return render(request, 'home/index.html', {
            'username_value': username,
            'field_errors': errors
        })

    try:
        # 3. Xác thực
        matched_user = User_Authentication.objects.filter(
            TenDangNhap=username, 
            MatKhau=password
        ).first()

        if matched_user:
            # Thành công -> Reset số lần sai
            request.session['failed_login_count'] = 0
            
            # Thiết lập session
            request.session['user_id']  = matched_user.UserID
            request.session['username'] = matched_user.TenDangNhap
            request.session['role']     = (matched_user.Vaitro or '').lower()
            
            # Ưu tiên lấy tên thật
            display_name = matched_user.TenDangNhap
            avatar_url = None
            
            if matched_user.Taixe and matched_user.Taixe.HoTen:
                display_name = matched_user.Taixe.HoTen
                avatar_url = matched_user.Taixe.HinhAnhURL
            elif matched_user.Nhaxe and matched_user.Nhaxe.TenNhaXe:
                display_name = matched_user.Nhaxe.TenNhaXe
                avatar_url = matched_user.Nhaxe.AnhDaiDienURL
            elif matched_user.KhachHang and matched_user.KhachHang.HovaTen:
                display_name = matched_user.KhachHang.HovaTen
                avatar_url = matched_user.KhachHang.AnhDaiDienURL
                
            request.session['ho_ten'] = display_name
            # KHÔNG ĐƯỢC LƯU avatar_url vào session vì nếu nó là chuỗi Base64 sẽ làm phình cookie vượt quá giới hạn 4KB của trình duyệt!
            # request.session['avatar'] = avatar_url
            
            if matched_user.Nhaxe:
                request.session['ma_nha_xe'] = matched_user.Nhaxe.NhaxeID
                request.session['ten_nha_xe'] = matched_user.Nhaxe.TenNhaXe
            
            request.session['token']    = 'direct-db-session'
            # request.session.set_expiry(0) # Tạm thời tắt để fix lỗi rớt session
            request.session.save() # Ép buộc lưu session vào Database trước khi redirect
            return _redirect_by_role(request.session['role'])
        else:
            # Sai -> Tăng số lần sai
            failed_count += 1
            request.session['failed_login_count'] = failed_count
            
            error_msg = 'Tên đăng nhập hoặc mật khẩu không đúng'
            if failed_count >= 5:
                return render(request, 'home/index.html', {
                    'username_value': username,
                    'is_locked': True,
                    'error_general': 'Bạn đã nhập sai mật khẩu trên 5 lần. Tài khoản của bạn đã bị khóa.'
                })
                
            return render(request, 'home/index.html', {
                'username_value': username,
                'field_errors': {
                    'username': 'Tên đăng nhập sai. Vui lòng nhập lại',
                    'password': 'Mật khẩu sai. Vui lòng nhập lại'
                }
            })
            
    except Exception as e:
        messages.error(request, f'Lỗi hệ thống: {str(e)}')
        return render(request, 'home/index.html', {'username_value': username})


def dangxuat(request):
    """Xoá session và quay về trang đăng nhập."""
    request.session.flush()
    return redirect('index')


# ==================== HELPER ====================

def _redirect_by_role(role: str):
    """
    Điều hướng người dùng theo role nhận từ API.
    Role hợp lệ: 'nhaxe' | 'taixe' | 'khachhang' (hoặc các alias).
    """
    ROLE_MAP = {
        'nhaxe':     'nhaxe',
        'nhà xe':    'nhaxe',
        'nx':        'nhaxe',
        'admin':     'admin_dashboard_quyet_toan',
        'taixe':     'taixe',
        'tài xế':    'taixe',
        'tx':        'taixe',
        'driver':    'taixe',
        'khachhang': 'khachhang',
        'khách hàng': 'khachhang',
        'kh':        'khachhang',
        'customer':  'khachhang',
    }
    url_name = ROLE_MAP.get(role, 'khachhang')  # mặc định → khách hàng
    return redirect(url_name)


# ==================== ĐĂNG KÝ & OTP ====================

def quen_mat_khau(request):
    return render(request, 'home/quen_mat_khau.html')

def dangky_khachhang(request):
    return render(request, 'home/dangky_khachhang.html')

def dangky_nhaxe(request):
    return render(request, 'home/dangky_nhaxe.html')


def send_registration_otp(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)
    
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        phone = data.get('phone')
        hoVaTen = data.get('hoVaTen')
        ngaySinh = data.get('ngaySinh')

        if not all([username, password, phone, hoVaTen, ngaySinh]):
            return JsonResponse({'status': 'error', 'message': 'Dữ liệu không đầy đủ.'}, status=400)
        
        if len(password) < 8:
            return JsonResponse({'status': 'error', 'message': 'Mật khẩu phải có ít nhất 8 ký tự.'}, status=400)
        
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', hoVaTen):
            return JsonResponse({'status': 'error', 'message': 'Họ tên không được chứa ký tự đặc biệt.'}, status=400)

        if User_Authentication.objects.filter(TenDangNhap=username).exists():
            return JsonResponse({'status': 'error', 'message': 'Tên đăng nhập đã tồn tại.'}, status=400)
        
        if User_Authentication.objects.filter(SoDienThoai=phone).exists():
            return JsonResponse({'status': 'error', 'message': 'Số điện thoại đã được sử dụng.'}, status=400)


        otp = str(random.randint(100000, 999999))
        request.session['registration_data'] = data
        request.session['registration_otp'] = otp
        request.session['otp_timestamp'] = time.time()
        
        print(f"SIMULATION: OTP for {phone} is {otp}")

        return JsonResponse({'status': 'success', 'message': 'OTP has been sent (simulation).'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': 'Lỗi hệ thống. Vui lòng thử lại sau!'}, status=500)

def verify_and_register(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)

    try:
        data = json.loads(request.body)
        otp_entered = str(data.get('otp', '')).strip()
        
        registration_data = request.session.get('registration_data')
        registration_otp = str(request.session.get('registration_otp', '')).strip()
        otp_timestamp = request.session.get('otp_timestamp')

        if not all([registration_data, registration_otp, otp_timestamp]):
            return JsonResponse({'status': 'error', 'message': 'Phiên đăng ký đã hết hạn. Vui lòng thử lại.'}, status=400)

        if time.time() - otp_timestamp > 180:
            del request.session['registration_data']
            del request.session['registration_otp']
            del request.session['otp_timestamp']
            return JsonResponse({'status': 'error', 'message': 'Mã OTP đã hết hạn. Vui lòng gửi lại mã.'}, status=400)

        if not otp_entered:
            return JsonResponse({'status': 'error', 'message': 'Vui lòng nhập mã OTP.'}, status=400)

        if otp_entered != registration_otp:
            return JsonResponse({'status': 'error', 'message': 'Mã xác thực không đúng.'}, status=400)

        with transaction.atomic():
            last_kh = KhachHang.objects.order_by('KhachHangID').last()
            new_kh_id = "KH00001"
            if last_kh:
                last_id_num = int(last_kh.KhachHangID[2:])
                new_id_num = last_id_num + 1
                new_kh_id = f"KH{new_id_num:05d}"

            KhachHang.objects.create(
                KhachHangID=new_kh_id,
                HovaTen=registration_data.get('hoVaTen'),
                NgaySinh=registration_data.get('ngaySinh'),
                Email=registration_data.get('email')
            )

            User_Authentication.objects.create(
                UserID=new_kh_id,
                TenDangNhap=registration_data.get('username'),
                MatKhau=registration_data.get('password'),
                Vaitro='Khách hàng',
                SoDienThoai=registration_data.get('phone'),
                KhachHang_id=new_kh_id
            )
        
        del request.session['registration_data']
        del request.session['registration_otp']
        del request.session['otp_timestamp']

        return JsonResponse({'status': 'success', 'message': 'Tạo tài khoản thành công!'})

    except Exception as e:
        print(f"Error during registration: {e}")
        return JsonResponse({'status': 'error', 'message': 'Lỗi hệ thống. Vui lòng thử lại sau!'}, status=500)


def send_registration_otp_nhaxe(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)
    
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        phone = data.get('phone')
        tenNhaXe = data.get('tenNhaXe')
        hotenDaiDien = data.get('hotenDaiDien')
        diaChiTruSo = data.get('diaChiTruSo')

        if not all([username, password, phone, tenNhaXe, hotenDaiDien, diaChiTruSo]):
            return JsonResponse({'status': 'error', 'message': 'Dữ liệu không đầy đủ.'}, status=400)
        
        if len(password) < 8:
            return JsonResponse({'status': 'error', 'message': 'Mật khẩu phải có ít nhất 8 ký tự.'}, status=400)
        
        if User_Authentication.objects.filter(TenDangNhap=username).exists():
            return JsonResponse({'status': 'error', 'message': 'Tên đăng nhập đã tồn tại.'}, status=400)
        
        if User_Authentication.objects.filter(SoDienThoai=phone).exists():
            return JsonResponse({'status': 'error', 'message': 'Số điện thoại đã được sử dụng.'}, status=400)
            
        if Nhaxe.objects.filter(SoDienThoai=phone).exists():
             return JsonResponse({'status': 'error', 'message': 'Số điện thoại đã được sử dụng.'}, status=400)

        otp = str(random.randint(100000, 999999))
        request.session['registration_data_nhaxe'] = data
        request.session['registration_otp_nhaxe'] = otp
        request.session['otp_timestamp_nhaxe'] = time.time()
        
        print(f"SIMULATION: OTP for Nha Xe {phone} is {otp}")

        return JsonResponse({'status': 'success', 'message': 'OTP has been sent (simulation).'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': 'Lỗi hệ thống. Vui lòng thử lại sau!'}, status=500)


def verify_and_register_nhaxe(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)

    try:
        data = json.loads(request.body)
        otp_entered = data.get('otp')
        
        registration_data = request.session.get('registration_data_nhaxe')
        registration_otp = request.session.get('registration_otp_nhaxe')
        otp_timestamp = request.session.get('otp_timestamp_nhaxe')

        if not all([registration_data, registration_otp, otp_timestamp]):
            return JsonResponse({'status': 'error', 'message': 'Phiên đăng ký đã hết hạn. Vui lòng thử lại.'}, status=400)

        if time.time() - otp_timestamp > 180:
            del request.session['registration_data_nhaxe']
            del request.session['registration_otp_nhaxe']
            del request.session['otp_timestamp_nhaxe']
            return JsonResponse({'status': 'error', 'message': 'Mã OTP đã hết hạn. Vui lòng gửi lại mã.'}, status=400)

        if not otp_entered:
            return JsonResponse({'status': 'error', 'message': 'Vui lòng nhập mã OTP.'}, status=400)

        if otp_entered != registration_otp:
            return JsonResponse({'status': 'error', 'message': 'Mã xác thực không đúng.'}, status=400)

        with transaction.atomic():
            last_nx = Nhaxe.objects.order_by('NhaxeID').last()
            new_nx_id = "NX00001"
            if last_nx:
                last_id_num = int(last_nx.NhaxeID[2:])
                new_id_num = last_id_num + 1
                new_nx_id = f"NX{new_id_num:05d}"

            new_nhaxe = Nhaxe.objects.create(
                NhaxeID=new_nx_id,
                TenNhaXe=registration_data.get('tenNhaXe'),
                DiaChiTruSo=registration_data.get('diaChiTruSo'),
                SoDienThoai=registration_data.get('phone'),
                Email=registration_data.get('email', f"{registration_data.get('username')}@example.com")
            )

            User_Authentication.objects.create(
                UserID=new_nx_id,
                TenDangNhap=registration_data.get('username'),
                MatKhau=registration_data.get('password'), 
                Vaitro='Nhaxe',
                SoDienThoai=registration_data.get('phone'),
                Nhaxe_id=new_nx_id
            )
            
            default_car_types = [
                {'id': 'LX00001', 'seats': 4, 'name': 'Xe 4 chỗ'},
                {'id': 'LX00002', 'seats': 7, 'name': 'Xe 7 chỗ'},
                {'id': 'LX00003', 'seats': 9, 'name': 'Xe 9 chỗ'},
            ]

            for car_type_data in default_car_types:
                loaixe_obj, created = Loaixe.objects.get_or_create(
                    LoaixeID=car_type_data['id'],
                    defaults={'SoCho': car_type_data['seats']}
                )
                CHITIETLOAIXE.objects.create(
                    Nhaxe=new_nhaxe,
                    Loaixe=loaixe_obj,
                    TenLoaiXe=car_type_data['name'],
                    GiaVe=0,
                    NgayCapNhatGia=datetime.now().date()
                )
        
        del request.session['registration_data_nhaxe']
        del request.session['registration_otp_nhaxe']
        del request.session['otp_timestamp_nhaxe']

        return JsonResponse({'status': 'success', 'message': 'Tạo tài khoản nhà xe thành công!'})

    except Exception as e:
        print(f"Error during nha xe registration: {e}")
        return JsonResponse({'status': 'error', 'message': 'Lỗi hệ thống. Vui lòng thử lại sau!'}, status=500)
