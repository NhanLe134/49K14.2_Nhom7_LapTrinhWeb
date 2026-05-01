from datetime import datetime, timedelta
import random
import json
import time
import re
from django.core.files.storage import default_storage
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.conf import settings
from django.db import transaction
from .models import ChuyenXe, Taixe, TuyenXe, Nhaxe, Xe, Loaixe, CHITIETLOAIXE, KhachHang, User_Authentication, Ve, GheNgoi, DanhGia

# ==================== TRANG CHUNG ====================

def timkiem(request):
    return render(request, 'home/timkiem.html')

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

        # Server-side validation
        if not all([username, password, phone, hoVaTen, ngaySinh]):
            return JsonResponse({'status': 'error', 'message': 'Dữ liệu không đầy đủ.'}, status=400)
        
        if len(password) < 8:
            return JsonResponse({'status': 'error', 'message': 'Mật khẩu phải có ít nhất 8 ký tự.'}, status=400)
        
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', hoVaTen): # Changed ho_va_ten to hoVaTen
            return JsonResponse({'status': 'error', 'message': 'Họ tên không được chứa ký tự đặc biệt.'}, status=400)

        if User_Authentication.objects.filter(TenDangNhap=username).exists():
            return JsonResponse({'status': 'error', 'message': 'Tên đăng nhập đã tồn tại.'}, status=400)
        
        if User_Authentication.objects.filter(SoDienThoai=phone).exists():
            return JsonResponse({'status': 'error', 'message': 'Số điện thoại đã được sử dụng.'}, status=400)

        if KhachHang.objects.filter(SoDienThoai=phone).exists():
             return JsonResponse({'status': 'error', 'message': 'Số điện thoại đã được sử dụng.'}, status=400)

        otp = str(random.randint(100000, 999999))
        request.session['registration_data'] = data
        request.session['registration_otp'] = otp
        request.session['otp_timestamp'] = time.time() # Lưu thời điểm tạo OTP
        
        print(f"SIMULATION: OTP for {phone} is {otp}")

        return JsonResponse({'status': 'success', 'message': 'OTP has been sent (simulation).'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Lỗi hệ thống. Vui lòng thử lại sau!'}, status=500)

def verify_and_register(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)

    try:
        data = json.loads(request.body)
        otp_entered = str(data.get('otp', '')).strip() # Convert to string and strip whitespace
        
        registration_data = request.session.get('registration_data')
        registration_otp = str(request.session.get('registration_otp', '')).strip() # Convert to string and strip whitespace
        otp_timestamp = request.session.get('otp_timestamp')

        print(f"DEBUG: verify_and_register - otp_entered: {otp_entered}, session_otp: {registration_otp}")

        if not all([registration_data, registration_otp, otp_timestamp]):
            return JsonResponse({'status': 'error', 'message': 'Phiên đăng ký đã hết hạn. Vui lòng thử lại.'}, status=400)

        # Kiểm tra OTP hết hạn (180 giây)
        if time.time() - otp_timestamp > 180:
            # Xóa session cũ để bảo mật
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
                MatKhau=registration_data.get('password'), # Cần mã hóa mật khẩu ở đây
                Vaitro='Khách hàng',
                SoDienThoai=registration_data.get('phone'),
                KhachHang_id=new_kh_id
            )
        
        del request.session['registration_data']
        del request.session['registration_otp']
        del request.session['otp_timestamp']

        return JsonResponse({'status': 'success', 'message': 'Tạo tài khoản thành công!'})

    except Exception as e:
        # Ghi lại lỗi ra log để debug
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

        # Server-side validation
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
        return JsonResponse({'status': 'error', 'message': f'Lỗi hệ thống. Vui lòng thử lại sau!'}, status=500)


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
                Email=registration_data.get('email', f"{registration_data.get('username')}@example.com") # Temp email if none
            )

            User_Authentication.objects.create(
                UserID=new_nx_id,
                TenDangNhap=registration_data.get('username'),
                MatKhau=registration_data.get('password'), 
                Vaitro='Nhaxe',
                SoDienThoai=registration_data.get('phone'),
                Nhaxe_id=new_nx_id
            )
            
            # --- Bổ sung logic khởi tạo loại xe mặc định cho nhà xe mới ---
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
                # Tạo CHITIETLOAIXE cho nhà xe mới với giá mặc định là 0
                CHITIETLOAIXE.objects.create(
                    Nhaxe=new_nhaxe,
                    Loaixe=loaixe_obj,
                    TenLoaiXe=car_type_data['name'], # Tên mặc định
                    GiaVe=0, # Giá khởi tạo là 0
                    NgayCapNhatGia=datetime.now().date()
                )
            # --- Kết thúc logic bổ sung ---
        
        del request.session['registration_data_nhaxe']
        del request.session['registration_otp_nhaxe']
        del request.session['otp_timestamp_nhaxe']

        return JsonResponse({'status': 'success', 'message': 'Tạo tài khoản nhà xe thành công!'})

    except Exception as e:
        print(f"Error during nha xe registration: {e}")
        return JsonResponse({'status': 'error', 'message': 'Lỗi hệ thống. Vui lòng thử lại sau!'}, status=500)


# ==================== KHÁCH HÀNG (kh) ====================

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

        # Check if phone or email is being updated and requires OTP
        phone_changed = (phone and phone != user_auth.SoDienThoai)
        email_changed = (email and email != kh.Email)

        if phone_changed or email_changed:
            update_otp = request.session.get('update_otp_khachhang')
            otp_timestamp = request.session.get('otp_timestamp_khachhang')

            print(f"DEBUG: capnhat_thongtin_khachhang - otp_entered: {otp_entered}, session_otp: {update_otp}")

            if not all([update_otp, otp_timestamp]):
                return JsonResponse({'status': 'error', 'message': 'Phiên xác thực đã hết hạn. Vui lòng gửi lại OTP.'}, status=400)

            if time.time() - otp_timestamp > 180: # OTP expires in 3 minutes
                del request.session['update_otp_khachhang']
                del request.session['otp_timestamp_khachhang']
                return JsonResponse({'status': 'error', 'message': 'Mã OTP đã hết hạn. Vui lòng gửi lại mã.'}, status=400)

            if not otp_entered or otp_entered != update_otp:
                return JsonResponse({'status': 'error', 'message': 'Mã OTP không chính xác.'}, status=400)

            # If OTP is correct, apply changes
            if phone_changed:
                if User_Authentication.objects.filter(SoDienThoai=phone).exclude(UserID=user_id).exists():
                    return JsonResponse({'status': 'error', 'message': 'Số điện thoại đã được sử dụng bởi tài khoản khác.'}, status=400)
                user_auth.SoDienThoai = phone
            if email_changed:
                if KhachHang.objects.filter(Email=email).exclude(KhachHangID=user_id).exists():
                    return JsonResponse({'status': 'error', 'message': 'Email đã được sử dụng bởi tài khoản khác.'}, status=400)
                kh.Email = email

            user_auth.save()
            # Clear OTP session data after successful verification
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

        # Check if the new phone/email is already in use by another user
        if phone and phone != user_auth.SoDienThoai:
            if User_Authentication.objects.filter(SoDienThoai=phone).exclude(UserID=user_id).exists():
                return JsonResponse({'status': 'error', 'message': 'Số điện thoại đã được sử dụng bởi tài khoản khác.'}, status=400)

        if email and email != khach_hang.Email:
            if KhachHang.objects.filter(Email=email).exclude(KhachHangID=user_id).exists():
                return JsonResponse({'status': 'error', 'message': 'Email đã được sử dụng bởi tài khoản khác.'}, status=400)

        otp = str(random.randint(100000, 999999))
        request.session['update_otp_khachhang'] = otp
        request.session['otp_timestamp_khachhang'] = time.time() # Store OTP generation time

        # In a real application, you would send this OTP via SMS or email
        print(f"SIMULATION: OTP for update (phone: {phone}, email: {email}) is {otp}")

        return JsonResponse({'status': 'success', 'message': 'Mã OTP đã được gửi (mô phỏng).'})
    except User_Authentication.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Không tìm thấy thông tin người dùng.'}, status=404)
    except KhachHang.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Không tìm thấy thông tin khách hàng.'}, status=404)
    except Exception as e:
        print(f"Error sending update OTP: {e}")
        return JsonResponse({'status': 'error', 'message': f'Lỗi hệ thống. Vui lòng thử lại sau!'}, status=500)


def lotrinh(request):
    trip_id = request.GET.get('id', '')
    if not trip_id:
        return redirect('nhaxe')

    try:
        chuyen = get_object_or_404(ChuyenXe.objects.select_related('TuyenXe', 'Xe'), pk=trip_id)
        ve_list = Ve.objects.filter(ChuyenXe_id=trip_id).select_related('Ghe')
    except Exception as e:
        messages.error(request, f"Lỗi: {e}")
        return redirect('nhaxe')

    return render(request, 'home/lotrinh.html', {
        'trip_id': trip_id,
        'chuyen': chuyen,
        've_list': ve_list
    })


def chitietchuyenxe(request):
    if request.method == 'POST':
        post_id = request.POST.get('id')
        new_status = request.POST.get('status')
        if post_id and new_status:
            try:
                ChuyenXe.objects.filter(pk=post_id).update(TrangThai=new_status)
                # Tự động cập nhật vé thành 'Đã đi' nếu chuyến xe hoàn thành
                if new_status == 'Hoàn thành':
                    Ve.objects.filter(ChuyenXe_id=post_id).update(TrangThai='Đã đi')
                messages.success(request, f'Đã cập nhật trạng thái thành "{new_status}".')
            except Exception as e:
                messages.error(request, f"Lỗi: {e}")
            return redirect(f"/chitietchuyenxe?id={post_id}")

    chuyenxe_id = request.GET.get('id')

    if not chuyenxe_id:
        return redirect('index')

    # Lấy thông tin chi tiết chuyến xe (GET)
    try:
        cx = get_object_or_404(ChuyenXe.objects.select_related('TuyenXe', 'Xe', 'Taixe'), pk=chuyenxe_id)

        # Format dữ liệu cho template
        if cx.TuyenXe:
            route_name = cx.TuyenXe.tenTuyen or "Chưa rõ"

        # Lấy số ghế set cứng theo loại xe (Loaixe.SoCho)
        total_seats = cx.Xe.Loaixe.SoCho if cx.Xe and cx.Xe.Loaixe else 0

        route_name = cx.TuyenXe.tenTuyen if cx.TuyenXe else "Chưa rõ"
        # Nếu tên tuyến chưa có thông tin điểm đi/đến thì mới nối thêm
        if cx.TuyenXe and cx.TuyenXe.diemDi and cx.TuyenXe.diemDen:
            if cx.TuyenXe.diemDi not in route_name or cx.TuyenXe.diemDen not in route_name:
                route_name = f"{cx.TuyenXe.tenTuyen} ({cx.TuyenXe.diemDi} - {cx.TuyenXe.diemDen})"


        # Chọn ảnh dựa trên số chỗ
        trip_image = "/static/img/xe1.jpg"
        if total_seats == 4: trip_image = "/static/img/xe4cho.jpeg"
        elif total_seats == 7: trip_image = "/static/img/xe7cho.jpg"
        elif total_seats == 9: trip_image = "/static/img/xe9cho.webp"

        # Tính giờ đến
        arrival_time_str = 'N/A'
        if cx.GioDi and cx.TuyenXe and cx.TuyenXe.ThoiGian:
            import datetime
            full_datetime = datetime.datetime.combine(datetime.date.today(), cx.GioDi)
            arrival_datetime = full_datetime + datetime.timedelta(hours=float(cx.TuyenXe.ThoiGian))
            arrival_time_str = arrival_datetime.strftime('%H:%M')
        elif cx.GioDen:
            arrival_time_str = cx.GioDen.strftime('%H:%M')

        trip_data = {
            'id': cx.ChuyenXeID,
            'driver': cx.Taixe.HoTen if cx.Taixe else None,
            'taixe_id': cx.Taixe.TaixeID if cx.Taixe else None,
            'route': route_name,
            'time': cx.GioDi.strftime('%H:%M') if cx.GioDi else 'N/A',
            'arrival_time': arrival_time_str,
            'carType': str(total_seats),
            'image': trip_image,
            'status': cx.TrangThai or 'Chưa hoàn thành'
        }
    except Exception as e:
        messages.error(request, f"Lỗi hiển thị chi tiết: {str(e)}")
        return redirect('quanlychuyenxe')


    ve_list = Ve.objects.filter(ChuyenXe_id=chuyenxe_id).select_related('Ghe')
    ticket_count = ve_list.count()
    available_seats = (cx.Xe.SoGhe - ticket_count) if cx.Xe and cx.Xe.SoGhe else 0

    # Cập nhật trip_data với available_seats
    trip_data['available_seats'] = available_seats

    # Lấy thông tin nhà xe để hiển thị header
    nha_xe_id = request.session.get('user_id')
    nha_xe_obj = None
    overdue_trips = []
    overdue_trips_count = 0
    if nha_xe_id:
        try:
            nha_xe_obj = Nhaxe.objects.get(NhaxeID=nha_xe_id)
            # Thông báo chuyến trễ
            from datetime import datetime
            today = datetime.now().date()
            # WORKAROUND cho TuyenXe_id
            overdue_trips = ChuyenXe.objects.filter(
                NgayKhoiHanh__lt=today,
                TrangThai='Chưa hoàn thành'
            ).select_related('TuyenXe')
            
            overdue_trips_list = [trip for trip in overdue_trips if trip.TuyenXe and getattr(trip.TuyenXe, 'nhaXe_id', getattr(trip.TuyenXe, 'nhaxe_id', None)) == nha_xe_id]
            overdue_trips_count = len(overdue_trips_list)
        except Exception:
            pass

    return render(request, 'home/chitietchuyenxe.html', {
        'trip_json': json.dumps(trip_data),
        'chuyenxe_id': chuyenxe_id,
        'trip_status': cx.TrangThai or 'Chưa hoàn thành',
        've_list': ve_list,
        'nha_xe': nha_xe_obj,
        'overdue_trips': overdue_trips_list if 'overdue_trips_list' in locals() else [],
        'overdue_trips_count': overdue_trips_count
    })


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
    # Lấy mã nhà xe từ session
    nha_xe_id = request.session.get('user_id')
    if not nha_xe_id:
        return redirect('dangnhap')

    try:
        # 1. Thông tin nhà xe
        nha_xe_obj = Nhaxe.objects.get(NhaxeID=nha_xe_id)

        # 2. Tính toán ngày trong tuần hiện tại (Thứ 2 - Chủ Nhật)
        today = datetime.now().date()
        start_of_week = today - timedelta(days=today.weekday())
        week_dates = []
        week_days_display = []
        day_names = ["Th 2", "Th 3", "Th 4", "Th 5", "Th 6", "Th 7", "CN"]

        for i in range(7):
            d = start_of_week + timedelta(days=i)
            week_dates.append(d)
            week_days_display.append({
                'day_name': day_names[i],
                'date_str': d.strftime('%d/%m'),
                'full_date': d.strftime('%Y-%m-%d'),
                'is_today': d == today
            })

        # 3. Lấy danh sách tài xế
        # WORKAROUND cho Nhaxe_id trong CHITIETTAIXE
        drivers_raw = Taixe.objects.all().prefetch_related('chitiettaixe_set')
        drivers_queryset = []
        for driver in drivers_raw:
            details = driver.chitiettaixe_set.all()
            for detail in details:
                 if getattr(detail, 'Nhaxe_id', getattr(detail, 'nhaxe_id', None)) == nha_xe_id:
                      drivers_queryset.append(driver)
                      break

        # 4. Lấy tất cả chuyến xe trong tuần này của nhà xe
        # WORKAROUND cho TuyenXe_id
        trips_queryset_raw = ChuyenXe.objects.filter(
            NgayKhoiHanh__range=[week_dates[0], week_dates[-1]]
        ).select_related('TuyenXe', 'Taixe')
        
        trips_queryset = [trip for trip in trips_queryset_raw if trip.TuyenXe and getattr(trip.TuyenXe, 'nhaXe_id', getattr(trip.TuyenXe, 'nhaxe_id', None)) == nha_xe_id]

        # 5. Tổ chức dữ liệu Lịch làm việc
        schedule_data = []
        active_drivers_today = set()
        total_completed = 0
        total_pending = 0

        for driver in drivers_queryset:
            driver_row = {
                'id': driver.TaixeID,
                'name': driver.HoTen or "Chưa đặt tên",
                'avatar': getattr(driver, 'HinhAnhURL', None) or "/static/img/default-avatar.png",
                'days': []
            }

            for d in week_dates:
                day_trips = []
                for cx in trips_queryset:
                    if cx.Taixe_id == driver.TaixeID and cx.NgayKhoiHanh == d:
                        day_trips.append({
                            'id': cx.ChuyenXeID,
                            'time': cx.GioDi.strftime('%H:%M') if cx.GioDi else '--:--',
                            'route': cx.TuyenXe.tenTuyen if cx.TuyenXe else 'N/A',
                            'status': cx.TrangThai
                        })

                        if d == today:
                            active_drivers_today.add(driver.TaixeID)

                        if cx.TrangThai == 'Hoàn thành':
                            total_completed += 1
                        else:
                            total_pending += 1

                driver_row['days'].append(day_trips)
            schedule_data.append(driver_row)

        # 6. Thống kê
        total_trips = total_completed + total_pending
        active_count = len(active_drivers_today)
        total_drivers = len(drivers_queryset)
        avg_trips = round(total_trips / total_drivers, 1) if total_drivers > 0 else 0

        context = {
            'nha_xe': nha_xe_obj,
            'week_days': week_days_display,
            'schedule': schedule_data,
        'avatar_url': nha_xe_obj.AnhDaiDienURL if nha_xe_obj else None,
            'stats': {
                'total_trips': total_trips,
                'total_completed': total_completed,
                'total_pending': total_pending,
                'active_drivers': active_count,
                'resting_drivers': total_drivers - active_count,
                'avg_trips': avg_trips
            }
        }
    except Exception as e:
        print(f"Error in nhaxe view: {e}")
        context = {'error': str(e)}

    return render(request, 'home/nhaxe.html', context)


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

        return render(request, 'home/thong_tin_nha_xe.html', {
            'nha_xe': nha_xe_obj,
            'avatar_url': nha_xe_obj.AnhDaiDienURL if nha_xe_obj else None
        })
    except Exception as e:
        messages.error(request, f'Lỗi hệ thống: {str(e)}')
        return redirect('nhaxe')


def quanly_loaixe(request):
    nha_xe_id = request.session.get('user_id')
    nha_xe_obj = get_object_or_404(Nhaxe, NhaxeID=nha_xe_id)

    # Thông báo chuyến trễ
    today = datetime.now().date()
    
    overdue_trips = ChuyenXe.objects.filter(
        NgayKhoiHanh__lt=today,
        TrangThai='Chưa hoàn thành'
    ).select_related('TuyenXe')
    
    # Lọc bằng python (list comprehension) để tránh issue ở CSDL khi truy vấn qua khóa ngoại có vấn đề case-sensitive
    # Việc này xử lý nhanh chóng mà không cần cấu hình lại CSDL
    overdue_trips_list = []
    for trip in overdue_trips:
        # Check an object level, Django will handle field mapping internally
        if trip.TuyenXe and getattr(trip.TuyenXe, 'nhaXe_id', getattr(trip.TuyenXe, 'nhaxe_id', None)) == nha_xe_id:
            overdue_trips_list.append(trip)
            
    overdue_trips_count = len(overdue_trips_list)

    # Lấy thông tin loại xe và giá từ CHITIETLOAIXE của nhà xe hiện tại
    loaixe_list_for_nhaxe = CHITIETLOAIXE.objects.filter(Nhaxe=nha_xe_obj).select_related('Loaixe')
    
    # Chuẩn bị dữ liệu để truyền vào template
    loaixe_data = []
    for ctlx in loaixe_list_for_nhaxe:
        loaixe_data.append({
            'LoaiXeId': ctlx.Loaixe.LoaixeID,
            'TenLoaiXe': ctlx.TenLoaiXe, # Lấy tên từ CHITIETLOAIXE
            'SoGhe': getattr(ctlx.Loaixe, 'SoCho', getattr(ctlx.Loaixe, 'socho', None)),
            'GiaVe': ctlx.GiaVe,
            'NgayCapNhat': ctlx.NgayCapNhatGia.strftime('%Y-%m-%d') if ctlx.NgayCapNhatGia else None
        })

    # Nếu muốn sắp xếp thì sort sau khi lấy dữ liệu lên python
    try:
        loaixe_data = sorted(loaixe_data, key=lambda x: x['SoGhe'] if x['SoGhe'] is not None else 0)
    except:
        pass

    return render(request, 'home/quanly_loaixe.html', {
        'loaixe_list': loaixe_data, # Đã đổi tên biến để tránh nhầm lẫn
        'nha_xe': nha_xe_obj,
        'avatar_url': nha_xe_obj.AnhDaiDienURL if nha_xe_obj else None,
        'overdue_trips': overdue_trips_list,
        'overdue_trips_count': overdue_trips_count
    })

def capnhat_gia_loaixe(request, pk):
    if request.method == 'POST':
        nha_xe_id = request.session.get('user_id')
        if not nha_xe_id:
            messages.error(request, "Bạn cần đăng nhập để thực hiện chức năng này.")
            return redirect('dangnhap')
            
        gia_moi = request.POST.get('gia_ve')
        try:
            # Tìm CHITIETLOAIXE của nhà xe hiện tại và loại xe được chọn
            chitiet_loaixe = get_object_or_404(CHITIETLOAIXE, Nhaxe_id=nha_xe_id, Loaixe_id=pk)
            chitiet_loaixe.GiaVe = gia_moi
            chitiet_loaixe.NgayCapNhatGia = datetime.now().date()
            chitiet_loaixe.save()
            messages.success(request, "Cập nhật giá vé thành công!")
        except Exception as e:
            messages.error(request, f"Lỗi cập nhật CSDL: {e}")
    return redirect('quanly_loaixe')

def quan_ly_xe(request):
    nha_xe_id = request.session.get('user_id')
    if not nha_xe_id:
        return redirect('dangnhap')
    
    nha_xe_obj = get_object_or_404(Nhaxe, NhaxeID=nha_xe_id)

    # Thông báo chuyến trễ
    today = datetime.now().date()
    # WORKAROUND cho TuyenXe_id
    overdue_trips = ChuyenXe.objects.filter(
        NgayKhoiHanh__lt=today,
        TrangThai='Chưa hoàn thành'
    ).select_related('TuyenXe')
    
    overdue_trips_list = [trip for trip in overdue_trips if trip.TuyenXe and getattr(trip.TuyenXe, 'nhaXe_id', getattr(trip.TuyenXe, 'nhaxe_id', None)) == nha_xe_id]
    overdue_trips_count = len(overdue_trips_list)

    if request.method == 'POST':
        action = request.POST.get('action')
        # ... logic xử lý POST giữ nguyên ...
        if action == 'delete':
            xe_id = request.POST.get('xe_id')
            Xe.objects.filter(XeID=xe_id, Nhaxe_id=nha_xe_id).delete()
            messages.success(request, "Đã xóa xe thành công.")
            return redirect('quan_ly_xe')

        # Thêm/Sửa
        bien_so = request.POST.get('bien_so')
        trang_thai = request.POST.get('trang_thai', 'Đang hoạt động')
        so_ghe = request.POST.get('so_ghe')
        loaixe_id = request.POST.get('loaixe_id')
        xe_id = request.POST.get('xe_id')
        hinh_anh = request.FILES.get('hinh_anh')

        try:
            if loaixe_id == 'new':
                # ... logic tạo loại xe mới ...
                new_loai_socho = request.POST.get('new_loai_socho')
                new_loai_gia = request.POST.get('new_loai_gia')
                last_loai = Loaixe.objects.order_by('-LoaixeID').first()
                if last_loai and str(last_loai.LoaixeID).startswith('LX'):
                    num = int(''.join(filter(str.isdigit, last_loai.LoaixeID))) + 1
                    loaixe_id = f"LX{num:05d}"
                else: loaixe_id = "LX00001"
                
                # Tạo Loaixe chung (nếu chưa có)
                loaixe_obj, created = Loaixe.objects.get_or_create(
                    LoaixeID=loaixe_id,
                    defaults={'SoCho': int(new_loai_socho)}
                )
                # Tạo CHITIETLOAIXE cho nhà xe hiện tại
                CHITIETLOAIXE.objects.create(
                    Nhaxe=nha_xe_obj,
                    Loaixe=loaixe_obj,
                    TenLoaiXe=f"Loại xe {new_loai_socho} chỗ",
                    GiaVe=new_loai_gia,
                    NgayCapNhatGia=today
                )

            if xe_id:
                xe = Xe.objects.filter(XeID=xe_id).first()
                if xe:
                    xe.BienSoXe, xe.TrangThai, xe.SoGhe, xe.Loaixe_id = bien_so, trang_thai, so_ghe, loaixe_id
                    if hinh_anh: xe.HinhAnhXe = hinh_anh
                    xe.save()
                messages.success(request, "Cập nhật xe thành công.")
            else:
                last_xe = Xe.objects.order_by('-XeID').first()
                new_xe_id = f"X{int(''.join(filter(str.isdigit, str(last_xe.XeID)))) + 1:05d}" if last_xe else "X00001"
                Xe.objects.create(XeID=new_xe_id, Nhaxe_id=nha_xe_id, BienSoXe=bien_so, TrangThai=trang_thai, SoGhe=so_ghe, Loaixe_id=loaixe_id, HinhAnhXe=hinh_anh)
                messages.success(request, "Thêm xe mới thành công.")
        except Exception as e: messages.error(request, f"Lỗi: {str(e)}")
        return redirect('quan_ly_xe')

    vehicles = Xe.objects.filter(Nhaxe_id=nha_xe_id).select_related('Loaixe')
    # Lấy các loại xe mà nhà xe này có CHITIETLOAIXE
    vehicle_types = Loaixe.objects.filter(chitietloaixe__Nhaxe=nha_xe_obj).distinct()
    return render(request, 'home/quan_ly_xe.html', {
        'vehicles': vehicles,
        'vehicle_types': vehicle_types,
        'nha_xe': nha_xe_obj,
        'avatar_url': nha_xe_obj.AnhDaiDienURL if nha_xe_obj else None,
        'overdue_trips': overdue_trips_list,
        'overdue_trips_count': overdue_trips_count
    })

def quanly_khachhang(request):
    nha_xe_id = request.session.get('user_id')
    nha_xe_obj = get_object_or_404(Nhaxe, NhaxeID=nha_xe_id) if nha_xe_id else None

    # Thông báo chuyến trễ
    overdue_trips_list = []
    overdue_trips_count = 0
    if nha_xe_id:
        today = datetime.now().date()
        # WORKAROUND cho TuyenXe_id
        overdue_trips = ChuyenXe.objects.filter(
            NgayKhoiHanh__lt=today,
            TrangThai='Chưa hoàn thành'
        ).select_related('TuyenXe')
        
        overdue_trips_list = [trip for trip in overdue_trips if trip.TuyenXe and getattr(trip.TuyenXe, 'nhaXe_id', getattr(trip.TuyenXe, 'nhaxe_id', None)) == nha_xe_id]
        overdue_trips_count = len(overdue_trips_list)

    khach_hang_data = User_Authentication.objects.filter(UserID=request.session.get('user_id')).first()
    avatar_url = None
    if nha_xe_obj:
        avatar_url = nha_xe_obj.AnhDaiDienURL
    elif khach_hang_data and khach_hang_data.KhachHang:
        avatar_url = khach_hang_data.KhachHang.AnhDaiDienURL

    return render(request, 'home/quanly_khachhang.html', {
        'khach_hang': khach_hang_data,
        'nha_xe': nha_xe_obj,
        'avatar_url': avatar_url,
        'overdue_trips': overdue_trips_list,
        'overdue_trips_count': overdue_trips_count
    })

def taixe_lotrinh(request):
    return render(request, 'home/taixe_lotrinh.html')

def phancongtaixe(request):
    nha_xe_id = request.session.get('user_id')
    nha_xe_obj = get_object_or_404(Nhaxe, NhaxeID=nha_xe_id)

    # Thông báo chuyến trễ
    today = datetime.now().date()
    # WORKAROUND cho TuyenXe_id
    overdue_trips = ChuyenXe.objects.filter(
        NgayKhoiHanh__lt=today,
        TrangThai='Chưa hoàn thành'
    ).select_related('TuyenXe')
    
    overdue_trips_list = [trip for trip in overdue_trips if trip.TuyenXe and getattr(trip.TuyenXe, 'nhaXe_id', getattr(trip.TuyenXe, 'nhaxe_id', None)) == nha_xe_id]
    overdue_trips_count = len(overdue_trips_list)

    # WORKAROUND cho Nhaxe_id trong CHITIETTAIXE
    taixe_list_raw = Taixe.objects.all().prefetch_related('chitiettaixe_set')
    taixe_list = []
    for driver in taixe_list_raw:
        details = driver.chitiettaixe_set.all()
        for detail in details:
             if getattr(detail, 'Nhaxe_id', getattr(detail, 'nhaxe_id', None)) == nha_xe_id:
                  taixe_list.append(driver)
                  break

    if request.method == 'POST':
        taixe_id = request.POST.get('taixe_id')
        chuyen_id = request.GET.get('id')
        if chuyen_id and taixe_id:
            cx = ChuyenXe.objects.filter(ChuyenXeID=chuyen_id).first()
            if cx:
                cx.Taixe_id = taixe_id
                cx.save()
                return JsonResponse({'status': 'success'})
        return JsonResponse({'status': 'error', 'message': 'Dữ liệu không hợp lệ'})

    return render(request, 'home/phancongtaixe.html', {
        'taixe_list': taixe_list,
        'nha_xe': nha_xe_obj,
        'avatar_url': getattr(nha_xe_obj, 'AnhDaiDienURL', None) if nha_xe_obj else None,
        'overdue_trips': overdue_trips_list,
        'overdue_trips_count': overdue_trips_count
    })