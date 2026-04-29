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
    View xử lý đăng nhập (Cả GET và POST):
    - GET: Hiển thị trang đăng nhập.
    - POST: Xác thực người dùng qua Database Supabase.
    """
    if request.method == 'GET':
        if request.session.get('user_id'):
            role = request.session.get('role', '')
            return _redirect_by_role(role)
        return render(request, 'home/index.html')

    # Xử lý đăng nhập trực tiếp qua Supabase (ORM)
    username = request.POST.get('username', '').strip()
    password = request.POST.get('password', '')
    
    if not username or not password:
        messages.error(request, 'Vui lòng nhập đầy đủ tên đăng nhập và mật khẩu.')
        return render(request, 'home/index.html', {'username_value': username})

    try:
        # Xác thực trực tiếp từ Database Supabase
        matched_user = User_Authentication.objects.filter(
            TenDangNhap=username, 
            MatKhau=password
        ).first()

        if matched_user:
            # Thiết lập session
            request.session['user_id']  = matched_user.UserID
            request.session['username'] = matched_user.TenDangNhap
            request.session['role']     = (matched_user.Vaitro or '').lower()
            request.session['ho_ten']   = matched_user.TenDangNhap
            
            # Lưu mã nhà xe vào session nếu là nhà xe
            if matched_user.Nhaxe:
                request.session['ma_nha_xe'] = matched_user.Nhaxe.NhaxeID
            
            request.session['token']    = 'direct-db-session'
            request.session.set_expiry(0)
            
            # messages.success(request, f'Chào mừng {username} quay trở lại!')
            return _redirect_by_role(request.session['role'])
        else:
            messages.error(request, 'Tên đăng nhập hoặc mật khẩu không đúng.')
    except Exception as e:
        messages.error(request, f'Lỗi kết nối database: {str(e)}')

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
