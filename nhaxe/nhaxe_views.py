from .decorators import nhaxe_required, taixe_required, khachhang_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from .models import Nhaxe, ChuyenXe, Taixe, Loaixe, CHITIETLOAIXE, User_Authentication, Xe
from datetime import datetime, timedelta
import random
import base64

@nhaxe_required
def nhaxe(request):
    nha_xe_id = request.session.get('ma_nha_xe')
    if not nha_xe_id:
        return redirect('dangnhap')

    try:
        nha_xe_obj = Nhaxe.objects.get(NhaxeID=nha_xe_id)
        try:
            week_offset = int(request.GET.get('week_offset', 0))
        except (ValueError, TypeError):
            week_offset = 0
        
        today = datetime.now().date()
        current_monday = today - timedelta(days=today.weekday())
        start_of_week = current_monday + timedelta(weeks=week_offset)
        
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

        drivers_raw = Taixe.objects.all().prefetch_related('chitiettaixe_set')
        drivers_queryset = []
        for driver in drivers_raw:
            details = driver.chitiettaixe_set.all()
            for detail in details:
                 if getattr(detail, 'Nhaxe_id', getattr(detail, 'nhaxe_id', None)) == nha_xe_id:
                      drivers_queryset.append(driver)
                      break

        trips_queryset_raw = ChuyenXe.objects.filter(
            NgayKhoiHanh__range=[week_dates[0], week_dates[-1]]
        ).select_related('TuyenXe', 'Taixe')
        
        trips_queryset = [trip for trip in trips_queryset_raw if trip.TuyenXe and getattr(trip.TuyenXe, 'nhaXe_id', getattr(trip.TuyenXe, 'nhaxe_id', None)) == nha_xe_id]

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

        total_trips = total_completed + total_pending
        active_count = len(active_drivers_today)
        total_drivers = len(drivers_queryset)
        avg_trips = round(total_trips / total_drivers, 1) if total_drivers > 0 else 0

        context = {
            'nha_xe': nha_xe_obj,
            'week_days': week_days_display,
            'schedule': schedule_data,
            'week_offset': week_offset,
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
        nha_xe_obj = None
        if nha_xe_id:
            try: nha_xe_obj = Nhaxe.objects.get(NhaxeID=nha_xe_id)
            except: pass
        context = {
            'error': str(e),
            'nha_xe': nha_xe_obj,
            'week_offset': week_offset if 'week_offset' in locals() else 0
        }

    return render(request, 'home/nhaxe.html', context)

@nhaxe_required
def thong_tin_nha_xe(request):
    user_id = request.session.get('ma_nha_xe')
    if not user_id:
        return redirect('dangnhap')

    nha_xe_obj = get_object_or_404(Nhaxe, NhaxeID=user_id)
    user_auth = User_Authentication.objects.filter(Nhaxe=nha_xe_obj).first()

    if request.method == 'POST':
        action = request.POST.get('action')
        if action in ['send_otp', 'send_phone_otp']:
            otp = str(random.randint(100000, 999999))
            request.session['update_otp'] = otp
            return JsonResponse({'status': 'success', 'message': f'[SIMULATION] Mã xác thực của bạn là: {otp}'})

        elif action == 'save':
            ten_nha_xe = request.POST.get('ten_nha_xe')
            representative = request.POST.get('representative')
            phone = request.POST.get('phone')
            address = request.POST.get('address')
            email = request.POST.get('email')
            password = request.POST.get('password')
            anh_dai_dien = request.FILES.get('anh_dai_dien')

            if phone and phone != nha_xe_obj.SoDienThoai:
                user_otp = request.POST.get('phone_otp')
                if user_otp != request.session.get('update_otp'):
                    return JsonResponse({'status': 'error', 'message': 'Mã xác thực không chính xác.'})

            nha_xe_obj.TenNhaXe = ten_nha_xe if ten_nha_xe else nha_xe_obj.TenNhaXe
            nha_xe_obj.NguoiDaiDien = representative if representative else nha_xe_obj.NguoiDaiDien
            nha_xe_obj.SoDienThoai = phone if phone else nha_xe_obj.SoDienThoai
            nha_xe_obj.DiaChiTruSo = address if address else nha_xe_obj.DiaChiTruSo
            if email: nha_xe_obj.Email = email
            if anh_dai_dien:
                try:
                    # Đọc file và chuyển sang base64
                    image_data = anh_dai_dien.read()
                    base64_data = base64.b64encode(image_data).decode('utf-8')
                    # Lấy extension
                    ext = anh_dai_dien.name.split('.')[-1].lower()
                    if ext not in ['jpg', 'jpeg', 'png', 'gif']:
                        ext = 'jpeg' # fallback
                    mime_type = f"image/{ext}" if ext != 'jpg' else "image/jpeg"
                    
                    nha_xe_obj.AnhDaiDienURL = f"data:{mime_type};base64,{base64_data}"
                except Exception as e:
                    print(f"Lỗi convert base64: {e}")

            nha_xe_obj.save()

            if password and user_auth:
                user_auth.password = password
                user_auth.save()

            return JsonResponse({'status': 'success', 'message': 'Cập nhật thông tin thành công!'})

    return render(request, 'home/thong_tin_nha_xe.html', {
        'nha_xe': nha_xe_obj,
        'user': user_auth,
        'avatar_url': nha_xe_obj.AnhDaiDienURL if nha_xe_obj else None
    })

@nhaxe_required
def quanly_loaixe(request):
    nha_xe_id = request.session.get('user_id')
    nha_xe_obj = get_object_or_404(Nhaxe, NhaxeID=nha_xe_id)
    today = datetime.now().date()
    
    overdue_trips = ChuyenXe.objects.filter(
        NgayKhoiHanh__lt=today,
        TrangThai='Chưa hoàn thành'
    ).select_related('TuyenXe')
    
    overdue_trips_list = [trip for trip in overdue_trips if trip.TuyenXe and getattr(trip.TuyenXe, 'nhaXe_id', getattr(trip.TuyenXe, 'nhaxe_id', None)) == nha_xe_id]
    overdue_trips_count = len(overdue_trips_list)

    loaixe_list_for_nhaxe = CHITIETLOAIXE.objects.filter(Nhaxe=nha_xe_obj).select_related('Loaixe')
    loaixe_data = []
    for ctlx in loaixe_list_for_nhaxe:
        loaixe_data.append({
            'LoaiXeId': ctlx.Loaixe.LoaixeID,
            'TenLoaiXe': ctlx.TenLoaiXe,
            'SoGhe': getattr(ctlx.Loaixe, 'SoCho', getattr(ctlx.Loaixe, 'socho', None)),
            'GiaVe': ctlx.GiaVe,
            'NgayCapNhat': ctlx.NgayCapNhatGia.strftime('%Y-%m-%d') if ctlx.NgayCapNhatGia else None
        })

    try:
        loaixe_data = sorted(loaixe_data, key=lambda x: x['SoGhe'] if x['SoGhe'] is not None else 0)
    except: pass

    return render(request, 'home/quanly_loaixe.html', {
        'loaixe_list': loaixe_data,
        'nha_xe': nha_xe_obj,
        'avatar_url': nha_xe_obj.AnhDaiDienURL if nha_xe_obj else None,
        'overdue_trips': overdue_trips_list,
        'overdue_trips_count': overdue_trips_count
    })

@nhaxe_required
def capnhat_gia_loaixe(request, pk):
    if request.method == 'POST':
        nha_xe_id = request.session.get('user_id')
        if not nha_xe_id:
            return redirect('dangnhap')
        gia_moi = request.POST.get('gia_ve')
        try:
            chitiet_loaixe = get_object_or_404(CHITIETLOAIXE, Nhaxe_id=nha_xe_id, Loaixe_id=pk)
            chitiet_loaixe.GiaVe = gia_moi
            chitiet_loaixe.NgayCapNhatGia = datetime.now().date()
            chitiet_loaixe.save()
            messages.success(request, "Cập nhật giá vé thành công!")
        except Exception as e:
            messages.error(request, f"Lỗi: {e}")
    return redirect('quanly_loaixe')

@nhaxe_required
def quan_ly_xe(request):
    nha_xe_id = request.session.get('ma_nha_xe')
    if not nha_xe_id: return redirect('dangnhap')
    nha_xe_obj = get_object_or_404(Nhaxe, NhaxeID=nha_xe_id)
    today = datetime.now().date()
    overdue_trips = ChuyenXe.objects.filter(NgayKhoiHanh__lt=today, TrangThai='Chưa hoàn thành').select_related('TuyenXe')
    overdue_trips_list = [trip for trip in overdue_trips if trip.TuyenXe and getattr(trip.TuyenXe, 'nhaXe_id', getattr(trip.TuyenXe, 'nhaxe_id', None)) == nha_xe_id]
    overdue_trips_count = len(overdue_trips_list)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'delete':
            xe_id = request.POST.get('xe_id')
            Xe.objects.filter(XeID=xe_id, Nhaxe_id=nha_xe_id).delete()
            messages.success(request, "Đã xóa xe thành công.")
            return redirect('quan_ly_xe')

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
                    num = int(''.join(filter(str.isdigit, last_loai.LoaixeID))) + 1
                    loaixe_id = f"LX{num:05d}"
                else: loaixe_id = "LX00001"
                
                loaixe_obj, created = Loaixe.objects.get_or_create(LoaixeID=loaixe_id, defaults={'SoCho': int(new_loai_socho)})
                CHITIETLOAIXE.objects.create(Nhaxe=nha_xe_obj, Loaixe=loaixe_obj, TenLoaiXe=f"Loại xe {new_loai_socho} chỗ", GiaVe=new_loai_gia, NgayCapNhatGia=today)

            if xe_id:
                xe = Xe.objects.filter(XeID=xe_id).first()
                if xe:
                    xe.BienSoXe, xe.TrangThai, xe.SoGhe, xe.Loaixe_id = bien_so, trang_thai, so_ghe, loaixe_id
                    if hinh_anh: xe.HinhAnhXe = hinh_anh
                    xe.save()
                messages.success(request, "Cập nhật xe thành công.")
            else:
                import re
                all_ids = Xe.objects.values_list('XeID', flat=True)
                max_num = 0
                for xid in all_ids:
                    nums = re.findall(r'\d+', str(xid))
                    if nums:
                        val = int(nums[-1])
                        if val > max_num:
                            max_num = val
                
                num = max_num + 1
                while True:
                    new_xe_id = f"XE{num:05d}"
                    if not Xe.objects.filter(XeID=new_xe_id).exists():
                        break
                    num += 1

                Xe.objects.create(XeID=new_xe_id, Nhaxe_id=nha_xe_id, BienSoXe=bien_so, TrangThai=trang_thai, SoGhe=so_ghe, Loaixe_id=loaixe_id, HinhAnhXe=hinh_anh)
                messages.success(request, "Thêm xe mới thành công.")
        except Exception as e: messages.error(request, f"Lỗi: {str(e)}")
        return redirect('quan_ly_xe')

    vehicles = Xe.objects.filter(Nhaxe_id=nha_xe_id).select_related('Loaixe')
    vehicle_types = CHITIETLOAIXE.objects.filter(Nhaxe_id=nha_xe_id, Loaixe__SoCho__in=[4, 7, 9, 16]).select_related('Loaixe')
    return render(request, 'home/quan_ly_xe.html', {
        'vehicles': vehicles,
        'vehicle_types': vehicle_types,
        'nha_xe': nha_xe_obj,
        'avatar_url': nha_xe_obj.AnhDaiDienURL if nha_xe_obj else None,
        'overdue_trips': overdue_trips_list,
        'overdue_trips_count': overdue_trips_count
    })

@nhaxe_required
def quanly_khachhang(request):
    nha_xe_id = request.session.get('user_id')
    nha_xe_obj = get_object_or_404(Nhaxe, NhaxeID=nha_xe_id) if nha_xe_id else None
    today = datetime.now().date()
    overdue_trips = ChuyenXe.objects.filter(NgayKhoiHanh__lt=today, TrangThai='Chưa hoàn thành').select_related('TuyenXe')
    overdue_trips_list = [trip for trip in overdue_trips if trip.TuyenXe and getattr(trip.TuyenXe, 'nhaXe_id', getattr(trip.TuyenXe, 'nhaxe_id', None)) == nha_xe_id]
    
    khach_hang_data = User_Authentication.objects.filter(UserID=request.session.get('user_id')).first()
    avatar_url = nha_xe_obj.AnhDaiDienURL if nha_xe_obj else (khach_hang_data.KhachHang.AnhDaiDienURL if khach_hang_data and khach_hang_data.KhachHang else None)

    return render(request, 'home/quanly_khachhang.html', {
        'khach_hang': khach_hang_data,
        'nha_xe': nha_xe_obj,
        'avatar_url': avatar_url,
        'overdue_trips': overdue_trips_list,
        'overdue_trips_count': len(overdue_trips_list)
    })
