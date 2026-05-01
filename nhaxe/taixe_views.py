from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from .models import Taixe, User_Authentication, CHITIETTAIXE, Nhaxe, ChuyenXe, Ve
from datetime import datetime, timedelta
import re

# ==================== NHÀ XE (Quản lý Tài Xế) ====================

def quanlytaixe(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('index')

    nha_xe_obj = get_object_or_404(Nhaxe, NhaxeID=user_id)
    
    # Thông báo chuyến trễ
    today = datetime.now().date()
    # WORKAROUND cho TuyenXe_id
    overdue_trips_raw = ChuyenXe.objects.filter(
        NgayKhoiHanh__lt=today,
        TrangThai='Chưa hoàn thành'
    ).select_related('TuyenXe')
    
    overdue_trips_list = [trip for trip in overdue_trips_raw if trip.TuyenXe and getattr(trip.TuyenXe, 'nhaXe_id', getattr(trip.TuyenXe, 'nhaxe_id', None)) == user_id]
    overdue_trips_count = len(overdue_trips_list)

    taixe_list = []
    
    # 1. Lấy tài xế thuộc nhà xe này (qua CHITIETTAIXE)
    # WORKAROUND cho Nhaxe_id trong CHITIETTAIXE
    drivers_raw = Taixe.objects.all().prefetch_related('chitiettaixe_set')
    drivers = []
    for driver in drivers_raw:
        # Lấy tất cả chi tiết tài xế cho driver này
        details = driver.chitiettaixe_set.all()
        for detail in details:
             if getattr(detail, 'Nhaxe_id', getattr(detail, 'nhaxe_id', None)) == user_id:
                  drivers.append(driver)
                  break

    users = {u.UserID: u for u in User_Authentication.objects.all()}

    # Tính toán mã ID mới
    max_num = 0
    for uid in users.keys():
        if uid.startswith('TAI') and uid[3:].isdigit():
            num = int(uid[3:])
            if num > max_num: max_num = num

    for driver in drivers:
        user_info = users.get(driver.TaixeID)
        taixe_list.append({
            'id':             driver.TaixeID,
            'ten':            driver.HoTen or (user_info.TenDangNhap if user_info else 'Chưa đặt tên'),
            'username':       user_info.TenDangNhap if user_info else '',
            'soDienThoai':    user_info.SoDienThoai if user_info else 'Chưa có',
            'soBangLai':      driver.SoBangLai,
            'soCCCD':         driver.soCCCD,
            'loaiBangLai':    driver.LoaiBangLai,
            'hinhAnh':        getattr(driver, 'HinhAnhURL', None),
        })
    
    ma_tai_xe_moi = f"TAI{max_num + 1:04d}"

    return render(request, 'home/quanlytaixe.html', {
        'taixe_list': taixe_list,
        'ma_tai_xe_moi': ma_tai_xe_moi,
        'nha_xe': nha_xe_obj,
        'avatar_url': getattr(nha_xe_obj, 'AnhDaiDienURL', None) if nha_xe_obj else None,
        'overdue_trips': overdue_trips_list,
        'overdue_trips_count': overdue_trips_count
    })

# ==================== THAO TÁC CRUD TÀI XẾ ====================

def them_tai_xe(request):
    """Tạo tài xế mới trực tiếp vào Database"""
    if request.method == 'POST':
        # 1. Lấy dữ liệu từ form
        username = request.POST.get('username')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        full_name = request.POST.get('full_name')
        phone = request.POST.get('phone')
        cccd = request.POST.get('cccd')
        license_no = request.POST.get('license_no')
        license_type = request.POST.get('license_type', 'B1')
        
        # 2. Validation
        if not all([username, password, full_name, phone, cccd, license_no]):
            messages.error(request, 'Vui lòng điền đầy đủ thông tin.')
            return redirect('quanlytaixe')
        if password != confirm_password:
            messages.error(request, 'Mật khẩu xác nhận không khớp.')
            return redirect('quanlytaixe')
            
        if User_Authentication.objects.filter(TenDangNhap=username).exists():
            messages.error(request, f"Lỗi: Tên đăng nhập '{username}' đã tồn tại.")
            return redirect('quanlytaixe')
            
        if User_Authentication.objects.filter(SoDienThoai=phone).exists():
            messages.error(request, f"Lỗi: Số điện thoại '{phone}' đã được đăng ký.")
            return redirect('quanlytaixe')

        from django.db import transaction
        try:
            with transaction.atomic():
                # 3. Tính ID mới
                all_uids = User_Authentication.objects.values_list('UserID', flat=True)
                max_num = 0
                for uid in all_uids:
                    if uid.startswith('TAI') and uid[3:].isdigit():
                        num = int(uid[3:])
                        if num > max_num: max_num = num
                new_id = f"TAI{max_num + 1:04d}"

                # 4. Lưu User
                nha_xe_id = request.session.get('user_id')
                new_user = User_Authentication(
                    UserID=new_id,
                    TenDangNhap=username,
                    MatKhau=password,
                    SoDienThoai=phone,
                    Vaitro="taixe",
                )
                if nha_xe_id:
                     setattr(new_user, 'Nhaxe_id', nha_xe_id)
                     if not hasattr(new_user, 'Nhaxe_id'):
                          setattr(new_user, 'nhaxe_id', nha_xe_id)

                new_user.save()

                # 5. Lưu Taixe
                new_driver = Taixe.objects.create(
                    TaixeID=new_id,
                    HoTen=full_name,
                    SoBangLai=license_no,
                    soCCCD=cccd,
                    LoaiBangLai=license_type,
                )

                # 6. Lưu CHITIETTAIXE
                ma_nha_xe = request.session.get('user_id')
                if ma_nha_xe:
                    Nhaxe_obj = Nhaxe.objects.get(NhaxeID=ma_nha_xe)
                    cttx = CHITIETTAIXE(
                        Nhaxe=Nhaxe_obj,
                        Taixe=new_driver,
                        HoTen=full_name,
                        NgayBatDau=datetime.now().date(),
                        NgayKetThuc=datetime(2099, 12, 31).date()
                    )
                    cttx.save()

            messages.success(request, f"Thêm tài xế {full_name} thành công.")
        except Exception as e:
            messages.error(request, f"Lỗi database: {str(e)}")
            
    return redirect('quanlytaixe')

def sua_tai_xe(request, pk):
    """Cập nhật thông tin tài xế trực tiếp vào Database"""
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        phone = request.POST.get('phone')
        license_no = request.POST.get('license_no')
        cccd = request.POST.get('cccd')
        license_type = request.POST.get('license_type', 'B1')
        
        from django.db import transaction
        try:
            full_name = request.POST.get('full_name')
            license_no = request.POST.get('license_no')
            cccd = request.POST.get('cccd')

            # 1. Cập nhật User
            User_Authentication.objects.filter(UserID=pk).update(
                SoDienThoai=phone
            )

            # 2. Cập nhật Taixe
            Taixe.objects.filter(TaixeID=pk).update(
                HoTen=full_name,
                SoBangLai=license_no,
                soCCCD=cccd,
                LoaiBangLai=license_type,
            )
            
            # 3. Cập nhật CHITIETTAIXE
            CHITIETTAIXE.objects.filter(Taixe_id=pk).update(HoTen=full_name)

            messages.success(request, f'Cập nhật thông tin tài xế thành công.')
        except Exception as e:
            messages.error(request, f'Lỗi database: {str(e)}')
            
    return redirect('quanlytaixe')

def xoa_tai_xe(request, pk):
    """Xóa tài xế trực tiếp khỏi Database"""
    if request.method == 'POST':
        try:
            # Xóa các liên kết trước nếu cần (Cascade trong model sẽ lo liệu nếu được setup)
            # Ở đây xóa tường minh để chắc chắn
            CHITIETTAIXE.objects.filter(Taixe_id=pk).delete()
            Taixe.objects.filter(TaixeID=pk).delete()
            User_Authentication.objects.filter(UserID=pk).delete()
            
            messages.success(request, 'Đã xóa tài xế khỏi hệ thống.')
        except Exception as e:
            messages.error(request, f'Lỗi khi xóa: {str(e)}')
            
    return redirect('quanlytaixe')

# Giữ lại các view tĩnh cũ (nếu có dùng)
def taixe(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('index')

    # 1. Lấy thông tin tài xế
    user_auth = User_Authentication.objects.filter(UserID=user_id).first()
    driver = user_auth.Taixe if user_auth else None
    
    if not driver:
        if user_auth and user_auth.Vaitro == 'Nhaxe':
            return redirect('nhaxe')

        messages.error(request, "Không tìm thấy thông tin tài xế. Vui lòng đăng nhập lại.")
        return redirect('index')
    
    # 2. Tính toán khoảng thời gian trong tuần (Thứ 2 -> Chủ Nhật)
    now = datetime.now()
    today = now.date()
    # today.weekday() trả về 0 (Thứ 2) -> 6 (Chủ Nhật)
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)

    # 3. Lấy danh sách chuyến xe trong tuần của tài xế
    trips_in_week = ChuyenXe.objects.filter(
        Taixe_id=user_id,
        NgayKhoiHanh__range=[start_of_week, end_of_week]
    ).select_related('TuyenXe').order_by('NgayKhoiHanh', 'GioDi')

    # 4. Nhóm chuyến xe theo các ngày trong tuần
    schedule_data = []
    days_in_week = [start_of_week + timedelta(days=i) for i in range(7)]
    dow_names = ['Th 2', 'Th 3', 'Th 4', 'Th 5', 'Th 6', 'Th 7', 'CN']

    for i, day in enumerate(days_in_week):
        day_trips = [t for t in trips_in_week if t.NgayKhoiHanh == day]
        schedule_data.append({
            'dow': dow_names[i],
            'date_str': day.strftime('%d-%m'),
            'is_today': day == today,
            'trips': day_trips,
            'has_morning_trip': any(t.GioDi.hour < 12 for t in day_trips),
            'has_afternoon_trip': any(t.GioDi.hour >= 12 for t in day_trips)
        })

    # 5. Thống kê & Nhà xe
    tong_tuan = trips_in_week.count()
    tong_hom_nay = trips_in_week.filter(NgayKhoiHanh=today).count()
    da_hoan_thanh_hom_nay = trips_in_week.filter(NgayKhoiHanh=today, TrangThai='Hoàn thành').count()
    da_hoan_thanh = ChuyenXe.objects.filter(Taixe_id=user_id, TrangThai='Hoàn thành').count()

    # Lấy thông tin tài xế & nhà xe để hiện Header
    nha_xe_obj = None
    taixe_obj = driver
    avatar_url = getattr(taixe_obj, 'HinhAnhURL', None) if taixe_obj else None
    detail = CHITIETTAIXE.objects.filter(Taixe_id=taixe_obj.TaixeID if taixe_obj else None).first()
    if detail:
        nha_xe_obj = detail.Nhaxe

    return render(request, 'home/taixe.html', {
        'schedule_data': schedule_data,
        'stats': {
            'tong_tuan': tong_tuan,
            'tong_hom_nay': tong_hom_nay,
            'da_hoan_thanh_hom_nay': da_hoan_thanh_hom_nay,
            'da_hoan_thanh': da_hoan_thanh
        },
        'nha_xe': nha_xe_obj,
        'ten_taixe': taixe_obj.HoTen if taixe_obj else None,
        'avatar_url': avatar_url
    })
def thongtin_taixe(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('index')

    user_auth = User_Authentication.objects.filter(UserID=user_id).first()
    driver = user_auth.Taixe if user_auth else None
    detail = CHITIETTAIXE.objects.filter(Taixe_id=driver.TaixeID if driver else None).first()

    if not driver or not user_auth:
        messages.error(request, "Không tìm thấy thông tin tài khoản.")
        return redirect('taixe')

    return render(request, 'home/thongtin_taixe.html', {
        'driver': driver,
        'user_auth': user_auth,
        'detail': detail,
        'nha_xe': detail.Nhaxe if detail else None,
        'ten_taixe': driver.HoTen if driver else None,
        'avatar_url': getattr(driver, 'HinhAnhURL', None) if driver else None
    })
def taixe_lotrinh(request):
    trip_id = request.GET.get('id', '')
    if not trip_id:
        return redirect('taixe')

    try:
        chuyen = get_object_or_404(ChuyenXe.objects.select_related('TuyenXe', 'Xe'), pk=trip_id)
        ve_list = Ve.objects.filter(ChuyenXe_id=trip_id).select_related('Ghe')
    except Exception as e:
        messages.error(request, f"Lỗi: {e}")
        return redirect('taixe')

    user_auth = User_Authentication.objects.filter(UserID=request.session.get('user_id')).first()
    taixe_obj = user_auth.Taixe if user_auth else None
    
    nha_xe_obj = None
    detail = CHITIETTAIXE.objects.filter(Taixe_id=taixe_obj.TaixeID if taixe_obj else None).first()
    if detail:
        nha_xe_obj = detail.Nhaxe

    return render(request, 'home/taixe_lotrinh.html', {
        'trip_id': trip_id,
        'chuyen': chuyen,
        've_list': ve_list,
        'nha_xe': nha_xe_obj,
        'ten_taixe': taixe_obj.HoTen if taixe_obj else None,
        'avatar_url': getattr(taixe_obj, 'HinhAnhURL', None) if taixe_obj else None
    })
def phancongtaixe(request):
    nha_xe_id = request.session.get('user_id')
    if not nha_xe_id:
        return redirect('dangnhap')

    nha_xe_obj = get_object_or_404(Nhaxe, NhaxeID=nha_xe_id)
    
    # Thông báo chuyến trễ
    today = datetime.now().date()
    # WORKAROUND cho TuyenXe_id
    overdue_trips_raw = ChuyenXe.objects.filter(
        NgayKhoiHanh__lt=today,
        TrangThai='Chưa hoàn thành'
    ).select_related('TuyenXe')
    
    overdue_trips = [trip for trip in overdue_trips_raw if trip.TuyenXe and getattr(trip.TuyenXe, 'nhaXe_id', getattr(trip.TuyenXe, 'nhaxe_id', None)) == nha_xe_id]
    overdue_trips_count = len(overdue_trips)

    trip_id = request.GET.get('id')
    if not trip_id:
        return redirect('quanlychuyenxe')

    # Xử lý khi phân công tài xế qua POST
    if request.method == 'POST':
        import traceback
        taixe_id = request.POST.get('taixe_id')
        try:
            if not trip_id:
                return JsonResponse({'status': 'error', 'message': 'Thiếu mã chuyến xe (trip_id).'})
            
            chuyen = ChuyenXe.objects.get(ChuyenXeID=trip_id)
            chuyen.Taixe_id = taixe_id
            chuyen.save()
            return JsonResponse({'status': 'success'})
        except Exception as e:
            error_trace = traceback.format_exc()
            print(f"Lỗi phân công tài xế:\n{error_trace}") 
            return JsonResponse({'status': 'error', 'message': f"{str(e)}\n\n{error_trace}"})

    # Lấy danh sách tài xế của nhà xe này
    taixe_list_raw = Taixe.objects.all().prefetch_related('chitiettaixe_set')
    taixe_list = []
    
    # Mapping SDT
    user_map = {u.UserID: u.SoDienThoai for u in User_Authentication.objects.all()}

    for driver in taixe_list_raw:
        details = driver.chitiettaixe_set.all()
        for detail in details:
            target_nhaxe = getattr(detail, 'Nhaxe_id', getattr(detail, 'nhaxe_id', None))
            if target_nhaxe == nha_xe_id:
                # Tính kinh nghiệm
                exp = 0
                if detail.NgayBatDau:
                    exp = datetime.now().year - detail.NgayBatDau.year
                driver.experience_years = exp if exp > 0 else 1
                driver.phone = user_map.get(driver.TaixeID, "Chưa có")
                taixe_list.append(driver)
                break
    
    return render(request, 'home/phancongtaixe.html', {
        'trip_id': trip_id,
        'taixe_list': taixe_list,
        'nha_xe': nha_xe_obj,
        'overdue_trips': overdue_trips,
        'overdue_trips_count': overdue_trips_count
    })