from datetime import datetime
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
from .models import ChuyenXe, Taixe, TuyenXe, Nhaxe, Xe, Loaixe, CHITIETLOAIXE, KhachHang, User_Authentication

# ==================== TRANG CHUNG ====================

def timkiem(request):
    return render(request, 'home/timkiem.html')

def quen_mat_khau(request):
    return render(request, 'home/quen_mat_khau.html')

def dangky_khachhang(request):
    return render(request, 'home/dangky_khachhang.html')

def send_registration_otp(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)
    
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        phone = data.get('phone')
        ho_va_ten = data.get('hoVaTen')

        # Server-side validation
        if not all([username, password, phone, ho_va_ten]):
            return JsonResponse({'status': 'error', 'message': 'Dữ liệu không đầy đủ.'}, status=400)
        
        if len(password) < 8:
            return JsonResponse({'status': 'error', 'message': 'Mật khẩu phải có ít nhất 8 ký tự.'}, status=400)
        
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', ho_va_ten):
            return JsonResponse({'status': 'error', 'message': 'Họ tên không được chứa ký tự đặc biệt.'}, status=400)

        if User_Authentication.objects.filter(TenDangNhap=username).exists():
            return JsonResponse({'status': 'error', 'message': 'Tên đăng nhập đã tồn tại.'}, status=400)
        
        if User_Authentication.objects.filter(SoDienThoai=phone).exists():
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
        otp_entered = data.get('otp')
        
        registration_data = request.session.get('registration_data')
        registration_otp = request.session.get('registration_otp')
        otp_timestamp = request.session.get('otp_timestamp')

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

            Nhaxe.objects.create(
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
                Vaitro='Nhà xe',
                SoDienThoai=registration_data.get('phone'),
                Nhaxe_id=new_nx_id
            )
        
        del request.session['registration_data_nhaxe']
        del request.session['registration_otp_nhaxe']
        del request.session['otp_timestamp_nhaxe']

        return JsonResponse({'status': 'success', 'message': 'Tạo tài khoản nhà xe thành công!'})

    except Exception as e:
        print(f"Error during nha xe registration: {e}")
        return JsonResponse({'status': 'error', 'message': 'Lỗi hệ thống. Vui lòng thử lại sau!'}, status=500)


def dangky_nhaxe(request):
    return render(request, 'home/dangky_nhaxe.html')

# ... (Các view khác giữ nguyên)
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

    return render(request, 'home/thongtin_khachhang.html', {'khach_hang': khach_hang_data})

def capnhat_thongtin_khachhang(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Phương thức không hợp lệ'}, status=405)

    user_id = request.session.get('user_id')
    if not user_id:
        return JsonResponse({'status': 'error', 'message': 'Người dùng chưa đăng nhập'}, status=401)

    try:
        hoten = request.POST.get('hoten')
        ngaysinh = request.POST.get('ngaysinh')
        avatar_file = request.FILES.get('avatar')

        kh, created = KhachHang.objects.get_or_create(KhachHangID=user_id)

        kh.HovaTen = hoten
        if ngaysinh:
            kh.NgaySinh = ngaysinh

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

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Lỗi phía server: {str(e)}'}, status=500)


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
    chuyenxe_id = request.GET.get('id')

    if not chuyenxe_id:
        return redirect('index')

    if request.method == 'POST':
        post_id = request.POST.get('id')
        new_status = request.POST.get('status')
        if post_id and new_status:
            try:
                ChuyenXe.objects.filter(pk=post_id).update(TrangThai=new_status)
                messages.success(request, f'Đã cập nhật trạng thái thành "{new_status}".')
            except Exception as e:
                messages.error(request, f"Lỗi: {e}")
            return redirect(f"/chitietchuyenxe?id={post_id}")

    try:
        cx = get_object_or_404(ChuyenXe.objects.select_related('TuyenXe', 'Xe', 'Taixe'), pk=chuyenxe_id)
        route_name = cx.TuyenXe.tenTuyen if cx.TuyenXe else "Chưa rõ"
        if cx.TuyenXe and cx.TuyenXe.diemDi and cx.TuyenXe.diemDen:
            route_name = f"{cx.TuyenXe.tenTuyen} ({cx.TuyenXe.diemDi} - {cx.TuyenXe.diemDen})"

        trip_data = {
            'id': cx.ChuyenXeID,
            'route': route_name,
            'time': cx.GioDi.strftime('%H:%M:%S') if cx.GioDi else '',
            'carType': str(cx.Xe.SoGhe) if cx.Xe else '4',
            'status': cx.TrangThai or 'pending',
            'driver': cx.Taixe.HoTen if cx.Taixe else 'Chưa phân công'
        }
    except Exception:
        messages.error(request, "Không tìm thấy thông tin chuyến xe.")
        return redirect('index')

    ve_list = Ve.objects.filter(ChuyenXe_id=chuyenxe_id).select_related('Ghe')

    return render(request, 'home/chitietchuyenxe.html', {
        'trip_json': json.dumps(trip_data),
        'chuyenxe_id': chuyenxe_id,
        'trip_status': cx.TrangThai or '',
        've_list': ve_list
    })


def vecuatoi(request):
    return render(request, 'home/vecuatoi.html')

def vietdanhgia(request):
    return render(request, 'home/vietdanhgia.html')

def dadanhgia(request):
    return render(request, 'home/dadanhgia.html')

def danhgiachuyenxe(request):
    return render(request, 'home/danhgiachuyenxe.html')

def nhaxe(request):
    try:
        trips_queryset = ChuyenXe.objects.select_related('TuyenXe', 'Taixe').all()
        formatted_trips = []
        for cx in trips_queryset:
            route_name = cx.TuyenXe.tenTuyen if cx.TuyenXe else "Chưa rõ"
            if cx.TuyenXe and cx.TuyenXe.diemDi and cx.TuyenXe.diemDen:
                route_name = f"{cx.TuyenXe.tenTuyen} ({cx.TuyenXe.diemDi} - {cx.TuyenXe.diemDen})"
            formatted_trips.append({
                'driver': cx.Taixe.HoTen if cx.Taixe else 'Chưa phân công',
                'date': cx.NgayKhoiHanh.strftime('%Y-%m-%d') if cx.NgayKhoiHanh else '',
                'time': cx.GioDi.strftime('%H:%M:%S') if cx.GioDi else '',
                'route': route_name
            })
        taixe_names = list(Taixe.objects.exclude(HoTen__isnull=True).values_list('HoTen', flat=True).distinct())
        unique_drivers = taixe_names if taixe_names else ['Chưa có tài xế']
    except Exception as e:
        print(f"Error in ORM nhaxe view: {e}")
        formatted_trips = []
        unique_drivers = ['Lỗi kết nối database']

    context = {
        'drivers_json': json.dumps(unique_drivers),
        'trips_json': json.dumps(formatted_trips)
    }
    return render(request, 'home/nhaxe.html', context)

def thong_tin_nha_xe(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('dangnhap')

    try:
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
                if phone and phone != nha_xe_obj.SoDienThoai:
                    user_otp = request.POST.get('otp')
                    if user_otp != request.session.get('update_otp'):
                        return JsonResponse({'status': 'error', 'message': 'Mã xác thực không chính xác.'})
                nha_xe_obj.SoDienThoai = phone if phone else nha_xe_obj.SoDienThoai
                nha_xe_obj.DiaChiTruSo = address if address else nha_xe_obj.DiaChiTruSo
                nha_xe_obj.save()
                return JsonResponse({'status': 'success', 'message': 'Cập nhật thông tin thành công!'})
        return render(request, 'home/thong_tin_nha_xe.html', {'nha_xe': nha_xe_obj})
    except Exception as e:
        messages.error(request, f'Lỗi hệ thống: {str(e)}')
        return redirect('nhaxe')


def quanly_loaixe(request):
    loaixe_list = [
        {'LoaiXeId': 'LX00001', 'TenLoaiXe': 'Loại xe A', 'SoGhe': '4', 'GiaVe': None, 'NgayCapNhat': None},
        {'LoaiXeId': 'LX00002', 'TenLoaiXe': 'Loại xe B', 'SoGhe': '7', 'GiaVe': None, 'NgayCapNhat': None},
        {'LoaiXeId': 'LX00003', 'TenLoaiXe': 'Loại xe C', 'SoGhe': '9', 'GiaVe': None, 'NgayCapNhat': None}
    ]
    try:
        api_data = Loaixe.objects.all()
        for xe_api in api_data:
            for xe_macdinh in loaixe_list:
                if str(xe_api.SoCho) == str(xe_macdinh['SoGhe']):
                    xe_macdinh['LoaiXeId'] = xe_api.LoaixeID
                    xe_macdinh['GiaVe'] = xe_api.GiaVe
                    xe_macdinh['NgayCapNhat'] = xe_api.NgayCapNhatGia.strftime('%Y-%m-%d') if xe_api.NgayCapNhatGia else None
    except Exception as e:
        print(f"Lỗi lấy dữ liệu từ database: {e}")
    return render(request, 'home/quanly_loaixe.html', {'loaixe_list': loaixe_list})


def capnhat_gia_loaixe(request, pk):
    if request.method == 'POST':
        gia_moi = request.POST.get('gia_ve')
        try:
            xe, created = Loaixe.objects.get_or_create(LoaixeID=pk)
            xe.GiaVe = gia_moi
            xe.NgayCapNhatGia = datetime.now().date()
            if created:
                so_cho = 4
                if pk == 'LX00002': so_cho = 7
                if pk == 'LX00003': so_cho = 9
                xe.SoCho = so_cho
            xe.save()
            messages.success(request, "Cập nhật giá vé thành công!")
        except Exception as e:
            messages.error(request, f"Lỗi cập nhật CSDL: {e}")
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
        hinh_anh = request.FILES.get('hinh_anh')

        try:
            if loaixe_id == 'new':
                new_loai_socho = request.POST.get('new_loai_socho')
                new_loai_gia = request.POST.get('new_loai_gia')
                
                last_loai = Loaixe.objects.order_by('-LoaixeID').first()
                if last_loai and str(last_loai.LoaixeID).startswith('LX'):
                    try:
                        num = int(''.join(filter(str.isdigit, last_loai.LoaixeID))) + 1
                        loaixe_id = f"LX{num:05d}"
                    except:
                        loaixe_id = "LX00001"
                else:
                    loaixe_id = "LX00001"
                
                Loaixe.objects.create(
                    LoaixeID=loaixe_id,
                    SoCho=int(new_loai_socho) if new_loai_socho else 4,
                    GiaVe=new_loai_gia if new_loai_gia else 0,
                    NgayCapNhatGia=datetime.now().date()
                )
                
                CHITIETLOAIXE.objects.create(
                    Nhaxe_id=nha_xe_id,
                    Loaixe_id=loaixe_id,
                    TenLoaiXe=f"Loại xe {new_loai_socho} chỗ"
                )

            if xe_id: # Sửa
                xe = Xe.objects.filter(XeID=xe_id).first()
                if xe:
                    xe.BienSoXe = bien_so
                    xe.TrangThai = trang_thai
                    xe.SoGhe = so_ghe
                    xe.Loaixe_id = loaixe_id
                    if hinh_anh:
                        xe.HinhAnhXe = hinh_anh
                    xe.save()
                messages.success(request, "Cập nhật xe thành công.")
            else: # Thêm mới
                last_xe = Xe.objects.order_by('-XeID').first()
                if last_xe:
                    try:
                        num = int(''.join(filter(str.isdigit, str(last_xe.XeID)))) + 1
                        new_xe_id = f"X{num:05d}"
                    except:
                        new_xe_id = "X00001"
                else:
                    new_xe_id = "X00001"

                xe = Xe(
                    XeID=new_xe_id,
                    Nhaxe_id=nha_xe_id,
                    BienSoXe=bien_so,
                    TrangThai=trang_thai,
                    SoGhe=so_ghe,
                    Loaixe_id=loaixe_id
                )
                if hinh_anh:
                    xe.HinhAnhXe = hinh_anh
                xe.save()
                messages.success(request, "Thêm xe mới thành công.")
        except Exception as e:
            messages.error(request, f"Lỗi: {str(e)}")

        return redirect('quan_ly_xe')

    vehicles = Xe.objects.filter(Nhaxe_id=nha_xe_id).select_related('Loaixe')
    vehicle_types = Loaixe.objects.all()
    return render(request, 'home/quan_ly_xe.html', {'vehicles': vehicles, 'vehicle_types': vehicle_types})

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
        ve_list = Ve.objects.filter(KhachHang_id=user_id).order_by('-NgayDat')
        return render(request, 'home/quanlyve.html', {'ve_list': ve_list})
    except Exception as e:
        messages.error(request, f"Lỗi lấy danh sách vé: {str(e)}")
        return render(request, 'home/quanlyve.html', {'ve_list': []})

def taixe(request):
    return render(request, 'home/taixe.html')

def thongtin_taixe(request):
    return render(request, 'home/thongtin_taixe.html')

def taixe_lotrinh(request):
    return render(request, 'home/taixe_lotrinh.html')

def phancongtaixe(request):
    return render(request, 'home/phancongtaixe.html')
