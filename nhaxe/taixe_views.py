from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Taixe, User_Authentication, CHITIETTAIXE, Nhaxe, ChuyenXe, Ve
from datetime import datetime, timedelta
import re

# ==================== NHÀ XE (Quản lý Tài Xế) ====================

def quanlytaixe(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('index')

    taixe_list = []
    
    # 1. Lấy tất cả tài xế và tài khoản từ Database (Supabase)
    users = {u.UserID: u for u in User_Authentication.objects.all()}
    drivers = Taixe.objects.all()

    # Tính toán mã ID mới
    max_num = 0
    # Quét qua UserID của mọi tài khoản để tìm số lớn nhất
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
            'hinhAnh':        driver.HinhAnhURL,
        })
    
    ma_tai_xe_moi = f"TAI{max_num + 1:04d}"

    return render(request, 'home/quanlytaixe.html', {
        'taixe_list': taixe_list,
        'ma_tai_xe_moi': ma_tai_xe_moi
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
        if password != confirm_password:
            messages.error(request, 'Mật khẩu xác nhận không khớp.')
            return redirect('quanlytaixe')
            
        if User_Authentication.objects.filter(TenDangNhap=username).exists():
            messages.error(request, f"Lỗi: Tên đăng nhập '{username}' đã tồn tại.")
            return redirect('quanlytaixe')
            
        if User_Authentication.objects.filter(SoDienThoai=phone).exists():
            messages.error(request, f"Lỗi: Số điện thoại '{phone}' đã được đăng ký.")
            return redirect('quanlytaixe')

        try:
            # 3. Tính ID mới
            all_uids = User_Authentication.objects.values_list('UserID', flat=True)
            max_num = 0
            for uid in all_uids:
                if uid.startswith('TAI') and uid[3:].isdigit():
                    num = int(uid[3:])
                    if num > max_num: max_num = num
            new_id = f"TAI{max_num + 1:04d}"

            # 4. Lưu User
            new_user = User_Authentication.objects.create(
                UserID=new_id,
                TenDangNhap=username,
                MatKhau=password,
                SoDienThoai=phone,
                Vaitro="taixe",
                Nhaxe_id=request.session.get('ma_nha_xe')
            )

            # 5. Lưu Taixe
            new_driver = Taixe.objects.create(
                TaixeID=new_id,
                HoTen=full_name,
                SoBangLai=license_no,
                soCCCD=cccd,
                LoaiBangLai=license_type,
            )

            # 6. Lưu CHITIETTAIXE
            ma_nha_xe = request.session.get('ma_nha_xe')
            if ma_nha_xe:
                Nhaxe_obj = Nhaxe.objects.get(NhaxeID=ma_nha_xe)
                CHITIETTAIXE.objects.create(
                    Nhaxe=Nhaxe_obj,
                    Taixe=new_driver,
                    HoTen=full_name,
                    NgayBatDau=datetime.now().date(),
                    NgayKetThuc=datetime(2099, 12, 31).date()
                )

            messages.success(request, f"Thêm tài xế {full_name} thành công.")
        except Exception as e:
            messages.error(request, f"Lỗi database: {str(e)}")
            
    return redirect('quanlytaixe')

def sua_tai_xe(request, pk):
    """Cập nhật thông tin tài xế trực tiếp vào Database"""
    if request.method == 'POST':
        phone = request.POST.get('phone')
        license_type = request.POST.get('license_type', 'B1')
        
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
    driver = get_object_or_404(Taixe, pk=user_id)
    
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
            'trips': day_trips
        })

    # 5. Tính toán thống kê
    # Tổng chuyến tuần
    tong_tuan = trips_in_week.count()
    
    # Tổng chuyến hôm nay
    tong_hom_nay = trips_in_week.filter(NgayKhoiHanh=today).count()
    
    # Tổng chuyến đã chạy (Hoàn thành) - tính tất cả thời gian
    da_hoan_thanh = ChuyenXe.objects.filter(Taixe_id=user_id, TrangThai='Hoàn thành').count()

    return render(request, 'home/taixe.html', {
        'schedule_data': schedule_data,
        'tong_tuan': tong_tuan,
        'tong_hom_nay': tong_hom_nay,
        'da_hoan_thanh': da_hoan_thanh
    })
def thongtin_taixe(request): return render(request, 'home/thongtin_taixe.html')
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

    return render(request, 'home/taixe_lotrinh.html', {
        'trip_id': trip_id,
        'chuyen': chuyen,
        've_list': ve_list
    })
def phancongtaixe(request): return render(request, 'home/phancongtaixe.html')