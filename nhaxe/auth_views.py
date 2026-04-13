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


@require_http_methods(['POST'])
def dangnhap(request):
    """
    View xử lý đăng nhập:
    1. Nhận username + password từ form POST.
    2. Gọi API backend để xác thực.
    3. Nếu thành công → lưu thông tin vào session → redirect theo role.
    4. Nếu thất bại → quay lại trang login với thông báo lỗi.
    """
    username = request.POST.get('username', '').strip()
    password = request.POST.get('password', '')

    # --- Validation cơ bản ---
    if not username or not password:
        messages.error(request, 'Vui lòng nhập đầy đủ tên đăng nhập và mật khẩu.')
        return render(request, 'home/index.html', {
            'username_value': username,
        })

    # --- Gọi API lấy danh sách tài khoản ---
    api_url = f"{settings.API_BASE_URL}/api/user-auth/"

    try:
        response = requests.get(
            api_url,
            timeout=settings.API_TIMEOUT,
        )
    except requests.exceptions.ConnectionError:
        messages.error(request, 'Không thể kết nối đến máy chủ. Vui lòng thử lại sau.')
        return render(request, 'home/index.html', {'username_value': username})
    except requests.exceptions.Timeout:
        messages.error(request, 'Máy chủ phản hồi quá chậm. Vui lòng thử lại.')
        return render(request, 'home/index.html', {'username_value': username})
    except requests.exceptions.RequestException as e:
        messages.error(request, f'Lỗi kết nối: {str(e)}')
        return render(request, 'home/index.html', {'username_value': username})

    # --- Xử lý phản hồi API ---
    if response.status_code == 200:
        try:
            users_data = response.json()
        except ValueError:
            messages.error(request, 'Phản hồi từ máy chủ không hợp lệ.')
            return render(request, 'home/index.html', {'username_value': username})

        # Tìm người dùng trong danh sách trả về
        matched_user = None
        for u in users_data:
            # API trả ra các key như UserID, TenDangNhap, MatKhau, Vaitro...
            if u.get('TenDangNhap') == username and u.get('MatKhau') == password:
                matched_user = u
                break
        
        if matched_user:
            # Lưu thông tin người dùng vào session
            request.session['user_id']  = matched_user.get('UserID')
            request.session['username'] = matched_user.get('TenDangNhap')
            request.session['role']     = (matched_user.get('Vaitro') or '').lower()
            request.session['ho_ten']   = matched_user.get('TenDangNhap')
            request.session['token']    = 'dummy-token' # API hiện tại không có JWT
            request.session.set_expiry(0)

            role = request.session['role']
            return _redirect_by_role(role)
        else:
            messages.error(request, 'Tên đăng nhập hoặc mật khẩu không đúng.')

    else:
        messages.error(request, f'Lấy dữ liệu API thất bại (mã lỗi: {response.status_code}).')

    return render(request, 'home/index.html', {'username_value': username})


def dangnhap_get(request):
    """Alias GET → trang đăng nhập (tránh 405 khi user vào thẳng /dangnhap)."""
    return redirect('index')


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
