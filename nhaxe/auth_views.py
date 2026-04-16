from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from django.views.decorators.http import require_http_methods
import requests


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
    - POST: Xác thực người dùng qua API.
    """
    if request.method == 'GET':
        if request.session.get('user_id'):
            role = request.session.get('role', '')
            return _redirect_by_role(role)
        return render(request, 'home/index.html')

    # Xử lý POST
    username = request.POST.get('username', '').strip()
    password = request.POST.get('password', '')
    
    # ... Rest of the existing POST logic ...
    if not username or not password:
        messages.error(request, 'Vui lòng nhập đầy đủ tên đăng nhập và mật khẩu.')
        return render(request, 'home/index.html', {'username_value': username})

    api_url = f"{settings.API_BASE_URL}/api/user-auth/"
    try:
        response = requests.get(api_url, timeout=settings.API_TIMEOUT)
    except requests.exceptions.Timeout:
        messages.error(request, 'Lỗi: Kết nối tới API quá hạn (Timeout). Vui lòng thử lại sau hoặc "đánh thức" server bằng cách truy cập link API trực tiếp.')
        return render(request, 'home/index.html', {'username_value': username})
    except Exception as e:
        messages.error(request, f'Lỗi kết nối API: {str(e)}')
        return render(request, 'home/index.html', {'username_value': username})

    if response.status_code == 200:
        users_data = response.json()
        matched_user = next((u for u in users_data if u.get('TenDangNhap') == username and u.get('MatKhau') == password), None)
        
        if matched_user:
            request.session['user_id']  = matched_user.get('UserID')
            request.session['username'] = matched_user.get('TenDangNhap')
            request.session['role']     = (matched_user.get('Vaitro') or '').lower()
            request.session['ho_ten']   = matched_user.get('TenDangNhap')
            request.session['token']    = 'dummy-token'
            request.session.set_expiry(0)
            return _redirect_by_role(request.session['role'])
        else:
            messages.error(request, 'Tên đăng nhập hoặc mật khẩu không đúng.')
    else:
        messages.error(request, f'Lấy dữ liệu API thất bại ({response.status_code}).')

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
