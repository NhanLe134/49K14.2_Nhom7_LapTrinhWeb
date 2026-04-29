from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from django.views.decorators.http import require_http_methods
from .models import User_Authentication

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
            if matched_user.Taixe and matched_user.Taixe.HoTen:
                display_name = matched_user.Taixe.HoTen
            elif matched_user.Nhaxe and matched_user.Nhaxe.TenNhaXe:
                display_name = matched_user.Nhaxe.TenNhaXe
                
            request.session['ho_ten'] = display_name
            
            if matched_user.Nhaxe:
                request.session['ma_nha_xe'] = matched_user.Nhaxe.NhaxeID
                request.session['ten_nha_xe'] = matched_user.Nhaxe.TenNhaXe
            
            request.session['token']    = 'direct-db-session'
            request.session.set_expiry(0)
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
        'nx':        'nhaxe',
        'admin':     'nhaxe',
        'taixe':     'taixe',
        'tx':        'taixe',
        'driver':    'taixe',
        'khachhang': 'khachhang',
        'kh':        'khachhang',
        'customer':  'khachhang',
    }
    url_name = ROLE_MAP.get(role, 'khachhang')  # mặc định → khách hàng
    return redirect(url_name)
