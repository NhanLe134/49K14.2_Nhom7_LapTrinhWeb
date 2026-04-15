from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
import requests

# ==================== NHÀ XE (Quản lý Tài Xế) ====================

def quanlytaixe(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('index')

    taixe_list = []

    try:
        # Lấy danh sách tài xế
        res_taixe = requests.get(
            f"{settings.API_BASE_URL}/api/taixe/",
            timeout=settings.API_TIMEOUT
        )
        
        # Lấy danh sách user-auth để map thêm thông tin sđt, username (nếu cần)
        res_user = requests.get(
            f"{settings.API_BASE_URL}/api/user-auth/",
            timeout=settings.API_TIMEOUT
        )
        
        if res_taixe.status_code == 200 and res_user.status_code == 200:
            taixe_raw = res_taixe.json()
            users_raw = res_user.json()
            
            # Tạo dictionary {UserID: UserInfo} để map nhanh
            user_dict = {u.get('UserID'): u for u in users_raw}

            for tx in taixe_raw:
                tx_id = tx.get('TaixeID', '')
                user_info = user_dict.get(tx_id, {})
                
                taixe_list.append({
                    'id':             tx_id,
                    'ten':            tx.get('HoTen') or user_info.get('TenDangNhap', tx_id),
                    'username':       user_info.get('TenDangNhap', ''),
                    'soDienThoai':    user_info.get('SoDienThoai', 'Chưa có'),
                    'soBangLai':      tx.get('SoBangLai', ''),
                    'soCCCD':         tx.get('soCCCD', ''),
                    'loaiBangLai':    tx.get('LoaiBangLai', ''),
                    'ngayHetHan':     tx.get('NgayHetHanBangLai', ''),
                    'hinhAnh':        tx.get('HinhAnhURL', ''),
                })
        else:
            messages.error(request, 'Lỗi lấy dữ liệu từ máy chủ API.')
    except requests.exceptions.Timeout:
        messages.error(request, 'Yêu cầu tới máy chủ bị quá hạn. Vui lòng thử lại.')
    except requests.exceptions.ConnectionError:
        messages.error(request, 'Không thể kết nối tới máy chủ API.')
    except requests.exceptions.RequestException as e:
        messages.error(request, f'Lỗi kết nối API: {str(e)}')

    return render(request, 'home/quanlytaixe.html', {'taixe_list': taixe_list})

# ==================== THAO TÁC CRUD TÀI XẾ ====================

def them_tai_xe(request):
    """
    Tạo tài xế mới:
    1. Tạo tài khoản User (auth)
    2. Tạo hồ sơ Taixe
    """
    if request.method == 'POST':
        # 1. Lấy dữ liệu từ form
        username = request.POST.get('username')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        full_name = request.POST.get('full_name')
        phone = request.POST.get('phone')
        cccd = request.POST.get('cccd')
        license_no = request.POST.get('license_no')
        license_type = request.POST.get('license_type')
        expiry_date = request.POST.get('expiry_date')
        
        # 2. Validation cơ bản
        if password != confirm_password:
            messages.error(request, 'Mật khẩu xác nhận không khớp.')
            return redirect('quanlytaixe')
            
        # 3. Tạo ID tự động (TAIxxxx)
        try:
            res_list = requests.get(f"{settings.API_BASE_URL}/api/taixe/", timeout=settings.API_TIMEOUT)
            max_num = 0
            if res_list.status_code == 200:
                for tx in res_list.json():
                    tid = tx.get('TaixeID', '')
                    if tid.startswith('TAI'):
                        try:
                            num = int(tid[3:])
                            if num > max_num: max_num = num
                        except ValueError:
                            pass
            new_id = f"TAI{max_num + 1:04d}"
        except:
            new_id = "TAI0001"

        # 4. Gọi API tạo User (Tài khoản)
        user_payload = {
            "UserID": new_id,
            "TenDangNhap": username,
            "MatKhau": password,
            "SoDienThoai": phone,
            "Vaitro": "taixe"
        }
        
        try:
            res_user = requests.post(f"{settings.API_BASE_URL}/api/user-auth/", json=user_payload, timeout=settings.API_TIMEOUT)
            if res_user.status_code not in [200, 201]:
                messages.error(request, f"Lỗi tạo tài khoản: {res_user.text}")
                return redirect('quanlytaixe')
                
            # 5. Gọi API tạo hồ sơ Taixe
            taixe_payload = {
                "TaixeID": new_id,
                "HoTen": full_name,
                "SoBangLai": license_no,
                "soCCCD": cccd,
                "LoaiBangLai": license_type,
                "NgayHetHanBangLai": expiry_date if expiry_date else None,
                "HinhAnhURL": "" 
            }
            
            res_taixe = requests.post(f"{settings.API_BASE_URL}/api/taixe/", json=taixe_payload, timeout=settings.API_TIMEOUT)
            
            if res_taixe.status_code in [200, 201]:
                messages.success(request, f"Thêm tài xế {full_name} thành công (ID: {new_id})")
            else:
                messages.error(request, f"Lỗi tạo hồ sơ tài xế: {res_taixe.text}")
        except Exception as e:
            messages.error(request, f"Lỗi kết nối API: {str(e)}")
            
    return redirect('quanlytaixe')


def sua_tai_xe(request, pk):
    """Cập nhật thông tin tài xế"""
    if request.method == 'POST':
        # 1. Lấy dữ liệu
        full_name = request.POST.get('full_name')
        phone = request.POST.get('phone') # Mặc dù chưa dùng ở form Edit, nhưng lấy ra nếu sau này cần map User
        license_no = request.POST.get('license_no')
        cccd = request.POST.get('cccd')
        license_type = request.POST.get('license_type')
        expiry_date = request.POST.get('expiry_date')

        # Dữ liệu cập nhật bảng taixe
        taixe_payload = {
            "TaixeID": pk,
            "HoTen": full_name,
            "SoBangLai": license_no,
            "soCCCD": cccd,
            "LoaiBangLai": license_type,
            "NgayHetHanBangLai": expiry_date if expiry_date else None,
        }
        
        try:
            # Lấy thông tin tài xế hiện tại (để lấy HinhAnhURL, nếu ko có có thể API báo lỗi null hoặc xóa mất)
            res_get = requests.get(f"{settings.API_BASE_URL}/api/taixe/{pk}/", timeout=settings.API_TIMEOUT)
            if res_get.status_code == 200:
                current_data = res_get.json()
                taixe_payload['HinhAnhURL'] = current_data.get('HinhAnhURL', '')
                # API của bạn có thể yêu cầu truyền đầy đủ các trường, ví dụ nếu k sửa HoTen thì lấy cũ
                if not full_name: taixe_payload['HoTen'] = current_data.get('HoTen', '')
                if not license_no: taixe_payload['SoBangLai'] = current_data.get('SoBangLai', '')
                if not cccd: taixe_payload['soCCCD'] = current_data.get('soCCCD', '')
                if not license_type: taixe_payload['LoaiBangLai'] = current_data.get('LoaiBangLai', '')

            # PUT bảng Taixe
            res_tx = requests.put(f"{settings.API_BASE_URL}/api/taixe/{pk}/", json=taixe_payload, timeout=settings.API_TIMEOUT)
            
            if res_tx.status_code in [200, 204]:
                messages.success(request, 'Cập nhật thông tin tài xế thành công.')
            else:
                messages.error(request, f'Cập nhật thất bại (Lỗi {res_tx.status_code}). Chi tiết: {res_tx.text}')
        except Exception as e:
            messages.error(request, f'Lỗi kết nối: {str(e)}')
            
    return redirect('quanlytaixe')


def xoa_tai_xe(request, pk):
    """Xóa tài xế"""
    if request.method == 'POST':
        try:
            # Xóa Taixe
            res_tx = requests.delete(f"{settings.API_BASE_URL}/api/taixe/{pk}/", timeout=settings.API_TIMEOUT)
            # Xóa User tương ứng
            requests.delete(f"{settings.API_BASE_URL}/api/user-auth/{pk}/", timeout=settings.API_TIMEOUT)
            
            if res_tx.status_code in [200, 204]:
                messages.success(request, 'Đã xóa tài xế khỏi hệ thống.')
            else:
                messages.error(request, f'Xóa thất bại trên server. (Lỗi {res_tx.status_code})')
        except Exception as e:
            messages.error(request, f'Lỗi khi xóa: {str(e)}')
            
    return redirect('quanlytaixe')

# ==================== TÀI XẾ (Màn hình của chính Tài Xế) ====================

def taixe(request):
    return render(request, 'home/taixe.html')

def thongtin_taixe(request):
    return render(request, 'home/thongtin_taixe.html')

def taixe_lotrinh(request):
    return render(request, 'home/taixe_lotrinh.html')

def phancongtaixe(request):
    return render(request, 'home/phancongtaixe.html')
