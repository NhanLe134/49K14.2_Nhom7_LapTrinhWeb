from datetime import datetime
import random
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.conf import settings
import json
from .models import ChuyenXe, Taixe, TuyenXe, Nhaxe, Xe, Loaixe, CHITIETLOAIXE, KhachHang, Ve, User_Authentication

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
    
    # Xử lý cập nhật trạng thái (POST) qua ORM
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

    # Lấy thông tin chi tiết chuyến xe (GET)
    try:
        cx = get_object_or_404(ChuyenXe.objects.select_related('TuyenXe', 'Xe', 'Taixe'), pk=chuyenxe_id)
        
        # Format dữ liệu cho template
        if cx.TuyenXe:
            route_name = cx.TuyenXe.tenTuyen or "Chưa rõ"
            
        # Lấy số ghế set cứng theo loại xe (Loaixe.SoCho)
        total_seats = cx.Xe.Loaixe.SoCho if cx.Xe and cx.Xe.Loaixe else 0

        trip_data = {
            'id': cx.ChuyenXeID,
            'route': route_name,
            'time': cx.GioDi.strftime('%H:%M:%S') if cx.GioDi else '',
            'carType': str(total_seats),
            'status': cx.TrangThai or 'Chưa hoàn thành',
            'driver': cx.Taixe.HoTen if cx.Taixe else 'Chưa phân công'
        }
    except Exception:
        messages.error(request, "Không tìm thấy thông tin chuyến xe.")
        return redirect('index')
            
    # Lấy danh sách hành khách từ bảng vé
    ve_list = Ve.objects.filter(ChuyenXe_id=chuyenxe_id).select_related('Ghe')
    ticket_count = ve_list.count()
    available_seats = (cx.Xe.SoGhe - ticket_count) if cx.Xe and cx.Xe.SoGhe else 0

    # Cập nhật trip_data với available_seats
    trip_data['available_seats'] = available_seats

    return render(request, 'home/chitietchuyenxe.html', {
        'trip_json': json.dumps(trip_data),
        'chuyenxe_id': chuyenxe_id,
        'trip_status': cx.TrangThai or 'Chưa hoàn thành',
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

# ==================== NHÀ XE (nx) ====================

def nhaxe(request):
    # Sử dụng Django ORM kết nối trực tiếp Supabase
    try:
        # Lấy danh sách chuyến xe và các thông tin liên quan (Optimize JOINs)
        trips_queryset = ChuyenXe.objects.select_related('TuyenXe', 'Taixe').all()
        
        formatted_trips = []
        for cx in trips_queryset:
            # Lấy tên lộ trình
            if cx.TuyenXe:
                route_name = cx.TuyenXe.tenTuyen or "Chưa rõ"
                
            formatted_trips.append({
                'driver': cx.Taixe.HoTen if cx.Taixe else 'Chưa phân công',
                'date': cx.NgayKhoiHanh.strftime('%Y-%m-%d') if cx.NgayKhoiHanh else '',
                'time': cx.GioDi.strftime('%H:%M:%S') if cx.GioDi else '',
                'route': route_name
            })
            
        # Lấy danh sách tên tài xế duy nhất
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
        
        return render(request, 'home/thong_tin_nha_xe.html', {'nha_xe': nha_xe_obj})
    except Exception as e:
        messages.error(request, f'Lỗi hệ thống: {str(e)}')
        return redirect('nhaxe')


def quanly_loaixe(request):
    # Danh sách 3 loại xe mặc định theo yêu cầu thiết kế
    loaixe_list = [
        {'LoaiXeId': 'LX00001', 'TenLoaiXe': 'Loại xe A', 'SoGhe': '4', 'GiaVe': None, 'NgayCapNhat': None},
        {'LoaiXeId': 'LX00002', 'TenLoaiXe': 'Loại xe B', 'SoGhe': '7', 'GiaVe': None, 'NgayCapNhat': None},
        {'LoaiXeId': 'LX00003', 'TenLoaiXe': 'Loại xe C', 'SoGhe': '9', 'GiaVe': None, 'NgayCapNhat': None}
    ]

    try:
        api_data = Loaixe.objects.all()
        for xe_api in api_data:
            api_id = xe_api.LoaixeID
            api_so_cho = xe_api.SoCho
            api_gia_ve = xe_api.GiaVe
            api_ngay_cap_nhat = xe_api.NgayCapNhatGia

            for xe_macdinh in loaixe_list:
                # Ghép dữ liệu dựa trên số chỗ ngồi (4, 7, 9)
                if str(api_so_cho) == str(xe_macdinh['SoGhe']):
                    xe_macdinh['LoaiXeId'] = api_id
                    xe_macdinh['GiaVe'] = api_gia_ve
                    xe_macdinh['NgayCapNhat'] = api_ngay_cap_nhat.strftime('%Y-%m-%d') if api_ngay_cap_nhat else None
    except Exception as e:
        print(f"Lỗi lấy dữ liệu từ database: {e}")

    return render(request, 'home/quanly_loaixe.html', {'loaixe_list': loaixe_list})


def capnhat_gia_loaixe(request, loaixe_id):
    if request.method == 'POST':
        gia_moi = request.POST.get('gia_ve')

        try:
            xe = Loaixe.objects.get(LoaixeID=loaixe_id)
            ngay_hien_tai = datetime.now().date()
            xe.GiaVe = gia_moi
            xe.NgayCapNhatGia = ngay_hien_tai
            xe.save()
            messages.success(request, "Cập nhật giá vé thành công!")
        except Loaixe.DoesNotExist:
            try:
                ngay_hien_tai = datetime.now().date()
                so_cho = 4
                if loaixe_id == 'LX00002': so_cho = 7
                if loaixe_id == 'LX00003': so_cho = 9
                Loaixe.objects.create(
                    LoaixeID=loaixe_id,
                    GiaVe=gia_moi,
                    NgayCapNhatGia=ngay_hien_tai,
                    SoCho=so_cho
                )
                messages.success(request, "Đã tạo mới và cập nhật giá vé thành công!")
            except Exception as e:
                 messages.error(request, f"Lỗi tạo mới loại xe: {e}")
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

        try:
            if xe_id: # Sửa
                Xe.objects.filter(XeID=xe_id).update(
                    BienSoXe=bien_so,
                    TrangThai=trang_thai,
                    SoGhe=so_ghe,
                    Loaixe_id=loaixe_id
                )
                messages.success(request, "Cập nhật xe thành công.")
            else: # Thêm mới
                Xe.objects.create(
                    Nhaxe_id=nha_xe_id,
                    BienSoXe=bien_so,
                    TrangThai=trang_thai,
                    SoGhe=so_ghe,
                    Loaixe_id=loaixe_id
                )
                messages.success(request, "Thêm xe mới thành công.")
        except Exception as e:
            messages.error(request, f"Lỗi: {str(e)}")
            
        return redirect('quan_ly_xe')

    # GET
    vehicles = Xe.objects.filter(Nhaxe_id=nha_xe_id)
    vehicle_types = Loaixe.objects.all()
    
    return render(request, 'home/quan_ly_xe.html', {
        'vehicles': vehicles,
        'vehicle_types': vehicle_types
    })

def quanly_khachhang(request):
    user_id = request.session.get('user_id')
    try:
        khach_hang_data = User_Authentication.objects.filter(UserID=user_id).first()
        return render(request, 'home/quanly_khachhang.html', {'khach_hang': khach_hang_data})
    except:
        return render(request, 'home/quanly_khachhang.html', {'khach_hang': None})

def quanlyve(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('index')
    try:
        from .models import DanhGia
        # Lấy vé của khách hàng
        all_ve = Ve.objects.filter(KhachHang_id=user_id).select_related('ChuyenXe', 'ChuyenXe__TuyenXe', 'ChuyenXe__Xe').order_by('-NgayDat')
        
        # Lấy ID các vé đã đánh giá
        ve_da_danh_gia_ids = list(DanhGia.objects.filter(KhachHang_id=user_id).values_list('Ve_id', flat=True))
        
        ve_booked = []
        ve_completed = []
        ve_cancelled = []
        
        for v in all_ve:
            # Map dữ liệu cho template
            v.ten_tuyen = v.ChuyenXe.TuyenXe.tenTuyen if v.ChuyenXe.TuyenXe else "Chưa rõ"
            v.ngay_khoi_hanh = v.ChuyenXe.NgayKhoiHanh.strftime('%d/%m/%Y') if v.ChuyenXe.NgayKhoiHanh else ""
            v.gio_di = v.ChuyenXe.GioDi.strftime('%H:%M') if v.ChuyenXe.GioDi else ""
            v.so_ghe = v.Ghe.soGhe if v.Ghe else "Đang chờ"
            v.da_danh_gia = v.VeID in ve_da_danh_gia_ids
            
            status = v.ChuyenXe.TrangThai
            if status == 'Hoàn thành':
                ve_completed.append(v)
            elif status == 'Đã hủy':
                ve_cancelled.append(v)
            else:
                ve_booked.append(v)

        return render(request, 'home/quanlyve.html', {
            've_booked': ve_booked,
            've_completed': ve_completed,
            've_cancelled': ve_cancelled
        })
    except Exception as e:
        messages.error(request, f"Lỗi lấy danh sách vé: {str(e)}")
        return render(request, 'home/quanlyve.html', {
            've_booked': [],
            've_completed': [],
            've_cancelled': []
        })

# ==================== TÀI XẾ (tx) ====================

def taixe(request):
    return render(request, 'home/taixe.html')

def thongtin_taixe(request):
    return render(request, 'home/thongtin_taixe.html')

def taixe_lotrinh(request):
    return render(request, 'home/taixe_lotrinh.html')

def phancongtaixe(request):
    return render(request, 'home/phancongtaixe.html')
