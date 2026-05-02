from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.core.files.storage import default_storage
from django.conf import settings
from .models import KhachHang, User_Authentication, Ve
import json
import time
import random

def khachhang(request):
    return render(request, 'home/khachhang.html')

def thongtin_khachhang(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('dangnhap')

    try:
        user_auth = User_Authentication.objects.get(UserID=user_id)
        khach_hang_data = {
            'KhachHangID': user_id,
            'HovaTen': user_auth.TenDangNhap,
            'SoDienThoai': user_auth.SoDienThoai,
            'Email': None,
            'NgaySinh': None,
            'AnhDaiDienURL': None,
        }
        try:
            kh = KhachHang.objects.get(KhachHangID=user_id)
            khach_hang_data.update({
                'HovaTen': kh.HovaTen or user_auth.TenDangNhap,
                'Email': kh.Email,
                'NgaySinh': kh.NgaySinh,
                'AnhDaiDienURL': kh.AnhDaiDienURL,
            })
        except KhachHang.DoesNotExist:
            pass

    except User_Authentication.DoesNotExist:
        messages.error(request, "Lỗi nghiêm trọng: Không tìm thấy thông tin xác thực người dùng.")
        return redirect('dangnhap')
    except Exception as e:
        messages.error(request, f"Đã xảy ra lỗi không mong muốn khi lấy dữ liệu: {e}")
        khach_hang_data = {
            'KhachHangID': user_id,
            'HovaTen': 'Lỗi dữ liệu',
            'SoDienThoai': 'N/A',
            'Email': None,
            'NgaySinh': None,
            'AnhDaiDienURL': None,
        }

    return render(request, 'home/thongtin_khachhang.html', {
        'khach_hang': khach_hang_data,
        'avatar_url': khach_hang_data.get('AnhDaiDienURL')
    })

def capnhat_thongtin_khachhang(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Phương thức không hợp lệ'}, status=405)

    user_id = request.session.get('user_id')
    if not user_id:
        return JsonResponse({'status': 'error', 'message': 'Người dùng chưa đăng nhập'}, status=401)

    try:
        hoten = request.POST.get('hoten')
        ngaysinh = request.POST.get('ngaysinh')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        otp_entered = request.POST.get('otp')

        kh, created = KhachHang.objects.get_or_create(KhachHangID=user_id)
        user_auth = User_Authentication.objects.get(UserID=user_id)

        phone_changed = (phone and phone != user_auth.SoDienThoai)
        email_changed = (email and email != kh.Email)

        if phone_changed or email_changed:
            update_otp = request.session.get('update_otp_khachhang')
            otp_timestamp = request.session.get('otp_timestamp_khachhang')

            if not all([update_otp, otp_timestamp]):
                return JsonResponse({'status': 'error', 'message': 'Phiên xác thực đã hết hạn. Vui lòng gửi lại OTP.'}, status=400)

            if time.time() - otp_timestamp > 180:
                del request.session['update_otp_khachhang']
                del request.session['otp_timestamp_khachhang']
                return JsonResponse({'status': 'error', 'message': 'Mã OTP đã hết hạn. Vui lòng gửi lại mã.'}, status=400)

            if not otp_entered or otp_entered != update_otp:
                return JsonResponse({'status': 'error', 'message': 'Mã OTP không chính xác.'}, status=400)

            if phone_changed:
                if User_Authentication.objects.filter(SoDienThoai=phone).exclude(UserID=user_id).exists():
                    return JsonResponse({'status': 'error', 'message': 'Số điện thoại đã được sử dụng bởi tài khoản khác.'}, status=400)
                user_auth.SoDienThoai = phone
            if email_changed:
                if KhachHang.objects.filter(Email=email).exclude(KhachHangID=user_id).exists():
                    return JsonResponse({'status': 'error', 'message': 'Email đã được sử dụng bởi tài khoản khác.'}, status=400)
                kh.Email = email

            user_auth.save()
            del request.session['update_otp_khachhang']
            del request.session['otp_timestamp_khachhang']

        kh.HovaTen = hoten
        if ngaysinh:
            kh.NgaySinh = ngaysinh

        avatar_file = request.FILES.get('avatar')
        avatar_url = None
        if avatar_file:
            file_name = default_storage.save(f"avatars/{avatar_file.name}", avatar_file)
            avatar_url = default_storage.url(file_name)
            kh.AnhDaiDienURL = avatar_url

        kh.save()

        # Cập nhật lại session để header hiển thị đúng tên mới
        request.session['ho_ten'] = kh.HovaTen
        request.session['avatar'] = kh.AnhDaiDienURL

        return JsonResponse({
            'status': 'success',
            'message': 'Cập nhật thông tin thành công!',
            'avatar_url': avatar_url
        })

    except User_Authentication.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Không tìm thấy thông tin người dùng.'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Lỗi phía server: {str(e)}'}, status=500)

def send_update_otp_khachhang(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)

    user_id = request.session.get('user_id')
    if not user_id:
        return JsonResponse({'status': 'error', 'message': 'Người dùng chưa đăng nhập.'}, status=401)

    try:
        data = json.loads(request.body)
        phone = data.get('phone')
        email = data.get('email')

        if not phone and not email:
            return JsonResponse({'status': 'error', 'message': 'Vui lòng cung cấp số điện thoại hoặc email để gửi OTP.'}, status=400)

        user_auth = User_Authentication.objects.get(UserID=user_id)
        khach_hang = KhachHang.objects.get(KhachHangID=user_id)

        if phone and phone != user_auth.SoDienThoai:
            if User_Authentication.objects.filter(SoDienThoai=phone).exclude(UserID=user_id).exists():
                return JsonResponse({'status': 'error', 'message': 'Số điện thoại đã được sử dụng bởi tài khoản khác.'}, status=400)

        if email and email != khach_hang.Email:
            if KhachHang.objects.filter(Email=email).exclude(KhachHangID=user_id).exists():
                return JsonResponse({'status': 'error', 'message': 'Email đã được sử dụng bởi tài khoản khác.'}, status=400)

        otp = str(random.randint(100000, 999999))
        request.session['update_otp_khachhang'] = otp
        request.session['otp_timestamp_khachhang'] = time.time()

        print(f"SIMULATION: OTP for update (phone: {phone}, email: {email}) is {otp}")

        return JsonResponse({'status': 'success', 'message': 'Mã OTP đã được gửi (mô phỏng).'})
    except User_Authentication.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Không tìm thấy thông tin người dùng.'}, status=404)
    except KhachHang.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Không tìm thấy thông tin khách hàng.'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Lỗi hệ thống. Vui lòng thử lại sau!'}, status=500)

def vecuatoi(request):
    """Trang xem vé của khách hàng - Alias cho quanlyve"""
    return redirect('quanlyve')
