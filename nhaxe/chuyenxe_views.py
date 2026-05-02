from .decorators import nhaxe_required, taixe_required, khachhang_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import ChuyenXe, TuyenXe, Xe, Taixe, Nhaxe, User_Authentication, Ve, GheNgoi, CHITIETTAIXE, CHITIETLOAIXE
from datetime import datetime
import random
import json



# ==================== NHÀ XE (nx) ====================

@nhaxe_required
def quanlychuyenxe(request):
    nha_xe_id = request.session.get('user_id')
    role = request.session.get('role', '').lower()
    
    if not nha_xe_id:
        return redirect('index')
    
    # Nếu là tài xế mà vào nhầm link nhà xe thì redirect về đúng trang của mình
    if role in ['taixe', 'tx', 'driver']:
        return redirect('taixe_quanlychuyenxe')

    try:
        from django.db.models import Count, Q
        nha_xe_obj = get_object_or_404(Nhaxe, NhaxeID=nha_xe_id)
        
        # Thông báo chuyến trễ
        today = datetime.now().date()
        overdue_trips_list = ChuyenXe.objects.filter(
            NgayKhoiHanh__lt=today,
            TrangThai='Chưa hoàn thành',
            TuyenXe__nhaXe_id=nha_xe_id
        ).select_related('TuyenXe')
        overdue_trips_count = overdue_trips_list.count()

        # Lọc chuyến xe thuộc nhà xe này (Sử dụng annotate để đếm vé thay vì vòng lặp N+1)
        trips = ChuyenXe.objects.filter(
            TuyenXe__nhaXe_id=nha_xe_id
        ).select_related('TuyenXe', 'Xe__Loaixe', 'Taixe').annotate(
            ticket_count=Count('ve')
        ).order_by('-ChuyenXeID')
        
        chuyen_xe_list = []
        for cx in trips:
            total_seats = cx.Xe.Loaixe.SoCho if cx.Xe and cx.Xe.Loaixe else 0
            chuyen_xe_list.append({
                'ChuyenXeID':   cx.ChuyenXeID,
                'route_name':   cx.TuyenXe.tenTuyen if cx.TuyenXe else '-',
                'gio_di_fmt':   cx.GioDi.strftime('%H:%M') if cx.GioDi else '-',
                'NgayKhoiHanh': cx.NgayKhoiHanh,
                'TrangThai':    cx.TrangThai or 'Chưa hoàn thành',
                'seat_count':   total_seats,
                'available_seats': (total_seats - cx.ticket_count) if total_seats > 0 else 0,
            })

        return render(request, 'home/quanlychuyenxe.html', {
            'chuyen_xe_list': chuyen_xe_list,
            'nha_xe': nha_xe_obj,
            'avatar_url': getattr(nha_xe_obj, 'AnhDaiDienURL', None) if nha_xe_obj else None,
            'overdue_trips': overdue_trips_list,
            'overdue_trips_count': overdue_trips_count
        })
    except Exception as e:
        messages.error(request, f'Lỗi lấy danh sách chuyến xe: {str(e)}')
        # Lấy lại nha_xe_obj thông minh hơn (xử lý cả trường hợp tài xế truy cập nhầm link)
        nha_xe_id = request.session.get('user_id')
        nha_xe_obj = None
        if nha_xe_id:
            try:
                # Thử tìm trực tiếp (nếu là chủ nhà xe)
                nha_xe_obj = Nhaxe.objects.get(NhaxeID=nha_xe_id)
            except Nhaxe.DoesNotExist:
                # Thử tìm qua tài xế (nếu là tài xế truy cập nhầm link nhà xe)
                from .models import CHITIETTAIXE
                detail = CHITIETTAIXE.objects.filter(Taixe_id=nha_xe_id).first()
                if detail:
                    nha_xe_obj = detail.Nhaxe
        return render(request, 'home/quanlychuyenxe.html', {
            'chuyen_xe_list': [],
            'nha_xe': nha_xe_obj
        })

@nhaxe_required
def themchuyenxe(request):
    nha_xe_id = request.session.get('user_id')
    if not nha_xe_id:
        return redirect('index')
    
    nha_xe_obj = get_object_or_404(Nhaxe, NhaxeID=nha_xe_id)
    
    # Thông báo chuyến trễ
    today = datetime.now().date()
    overdue_trips_list = ChuyenXe.objects.filter(
        NgayKhoiHanh__lt=today,
        TrangThai='Chưa hoàn thành',
        TuyenXe__nhaXe_id=nha_xe_id
    ).select_related('TuyenXe')
    overdue_trips_count = overdue_trips_list.count()
        
    if request.method == 'POST':
        tuyen_id = request.POST.get('tuyenxe')
        xe_id = request.POST.get('xe')
        ngay = request.POST.get('date')
        gio = request.POST.get('time')
        
        try:
            ChuyenXe.objects.create(
                TuyenXe_id=tuyen_id,
                Xe_id=xe_id,
                Taixe=None,
                NgayKhoiHanh=ngay,
                GioDi=gio,
                TrangThai='Chưa hoàn thành'
            )
            messages.success(request, 'Thêm chuyến xe thành công.')
            return redirect('quanlychuyenxe')
        except Exception as e:
            messages.error(request, f'Lỗi khi thêm chuyến xe: {str(e)}')

    tuyen_xe_list = TuyenXe.objects.filter(nhaXe_id=nha_xe_id)
    xe_list = Xe.objects.filter(Nhaxe_id=nha_xe_id)
    
    # Lấy danh sách tài xế thuộc nhà xe này qua bảng trung gian CHITIETTAIXE
    taixe_list = Taixe.objects.filter(chitiettaixe__Nhaxe_id=nha_xe_id).distinct()
    
    return render(request, 'home/themchuyenxe.html', {
        'tuyen_xe_list': tuyen_xe_list,
        'xe_list': xe_list,
        'taixe_list': taixe_list,
        'nha_xe': nha_xe_obj,
        'avatar_url': getattr(nha_xe_obj, 'AnhDaiDienURL', None) if nha_xe_obj else None,
        'overdue_trips': overdue_trips_list,
        'overdue_trips_count': overdue_trips_count
    })

@nhaxe_required
def suachuyenxe(request, pk):
    nha_xe_id = request.session.get('user_id')
    if not nha_xe_id:
        return redirect('index')

    nha_xe_obj = get_object_or_404(Nhaxe, NhaxeID=nha_xe_id)
    
    # Thông báo chuyến trễ
    today = datetime.now().date()
    overdue_trips_list = ChuyenXe.objects.filter(
        NgayKhoiHanh__lt=today,
        TrangThai='Chưa hoàn thành',
        TuyenXe__nhaXe_id=nha_xe_id
    ).select_related('TuyenXe')
    overdue_trips_count = overdue_trips_list.count()

    chuyen = get_object_or_404(ChuyenXe, ChuyenXeID=pk)

    if request.method == 'POST':
        try:
            chuyen.TuyenXe_id = request.POST.get('tuyenxe')
            chuyen.Xe_id = request.POST.get('xe')
            chuyen.Taixe_id = request.POST.get('taixe')
            chuyen.NgayKhoiHanh = request.POST.get('date')
            chuyen.GioDi = request.POST.get('time')
            if request.POST.get('trangthai'):
                chuyen.TrangThai = request.POST.get('trangthai')
                if chuyen.TrangThai == 'Hoàn thành':
                    Ve.objects.filter(ChuyenXe_id=chuyen.ChuyenXeID).update(TrangThai='Đã đi', TrangThaiThanhToan='Đã thanh toán')
            chuyen.save()
            messages.success(request, 'Sửa chuyến xe thành công.')
            return redirect('quanlychuyenxe')
        except Exception as e:
            messages.error(request, f'Lỗi khi cập nhật: {str(e)}')

    tuyen_xe_list = TuyenXe.objects.filter(nhaXe_id=nha_xe_id)
    xe_list = Xe.objects.filter(Nhaxe_id=nha_xe_id)
    
    # Lấy danh sách tài xế thuộc nhà xe này qua bảng trung gian CHITIETTAIXE
    taixe_list = Taixe.objects.filter(chitiettaixe__Nhaxe_id=nha_xe_id).distinct()
    
    if isinstance(chuyen.NgayKhoiHanh, str): formatted_date = chuyen.NgayKhoiHanh
    else: formatted_date = chuyen.NgayKhoiHanh.strftime('%Y-%m-%d') if chuyen.NgayKhoiHanh else ''
        
    if isinstance(chuyen.GioDi, str): formatted_time = chuyen.GioDi
    else: formatted_time = chuyen.GioDi.strftime('%H:%M') if chuyen.GioDi else ''

    return render(request, 'home/suachuyenxe.html', {
        'chuyen': chuyen,
        'formatted_date': formatted_date,
        'formatted_time': formatted_time,
        'tuyen_xe_list': tuyen_xe_list,
        'xe_list': xe_list,
        'taixe_list': taixe_list,
        'nha_xe': nha_xe_obj,
        'overdue_trips': overdue_trips_list,
        'overdue_trips_count': overdue_trips_count
    })

@nhaxe_required
def hoanthanh_chuyenxe(request, pk):
    """Cập nhật trạng thái chuyến xe thành 'Hoàn thành'."""
    if request.method == 'POST':
        try:
            ChuyenXe.objects.filter(pk=pk).update(TrangThai='Hoàn thành')
            Ve.objects.filter(ChuyenXe_id=pk).update(TrangThai='Đã đi', TrangThaiThanhToan='Đã thanh toán')
            messages.success(request, 'Đã cập nhật trạng thái: Hoàn thành.')
        except Exception as e:
            messages.error(request, f'Lỗi: {str(e)}')
    return redirect(f"/chitietchuyenxe?id={pk}")

# ==================== TÀI XẾ (tx) ====================

@taixe_required
def taixe_quanlychuyenxe(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('index')

    try:
        from django.db.models import Count
        user_auth = User_Authentication.objects.filter(UserID=user_id).first()
        taixe_obj = user_auth.Taixe if user_auth else None
        
        nha_xe_obj = None
        detail = CHITIETTAIXE.objects.filter(Taixe_id=taixe_obj.TaixeID if taixe_obj else None).first()
        if detail:
            nha_xe_obj = detail.Nhaxe

        trips = ChuyenXe.objects.filter(Taixe_id=user_id)\
                                .select_related('TuyenXe', 'Xe')\
                                .annotate(ticket_count=Count('ve'))\
                                .order_by('-NgayKhoiHanh', '-GioDi')
        
        chuyen_xe_list = []
        for cx in trips:
            total_seats = cx.Xe.Loaixe.SoCho if cx.Xe and cx.Xe.Loaixe else 0
            chuyen_xe_list.append({
                'ChuyenXeID':   cx.ChuyenXeID,
                'route_name':   cx.TuyenXe.tenTuyen if cx.TuyenXe else f"{cx.TuyenXe.diemDi} - {cx.TuyenXe.diemDen}" if cx.TuyenXe else "-",
                'gio_di_fmt':   cx.GioDi.strftime('%H:%M') if cx.GioDi else '-',
                'seat_count':   total_seats,
                'available_seats': (total_seats - cx.ticket_count) if total_seats > 0 else 0,
                'TrangThai':    cx.TrangThai or 'Chưa hoàn thành',
            })
        return render(request, 'home/taixe_quanlychuyenxe.html', {
            'chuyen_xe_list': chuyen_xe_list,
            'nha_xe': nha_xe_obj,
            'ten_taixe': taixe_obj.HoTen if taixe_obj else None,
            'avatar_url': getattr(taixe_obj, 'HinhAnhURL', None) if taixe_obj else None
        })
    except Exception:
        # Fallback nha_xe retrieval
        nha_xe_obj = None
        user_id = request.session.get('user_id')
        if user_id:
            detail = CHITIETTAIXE.objects.filter(Taixe_id=user_id).first()
            if detail: nha_xe_obj = detail.Nhaxe
            
        return render(request, 'home/taixe_quanlychuyenxe.html', {
            'chuyen_xe_list': [],
            'nha_xe': nha_xe_obj,
            'ten_taixe': request.session.get('username')
        })

@taixe_required
def taixe_chitietchuyenxe(request):
    """Chi tiết chuyến xe cho tài xế."""
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('index')
        
    chuyenxe_id = request.POST.get('id') or request.GET.get('id')
    if not chuyenxe_id:
        return redirect('taixe_quanlychuyenxe')

    chuyen = get_object_or_404(ChuyenXe, ChuyenXeID=chuyenxe_id, Taixe_id=user_id)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status:
            try:
                chuyen.TrangThai = new_status
                chuyen.save()
                
                # Tự động cập nhật vé nếu hoàn thành
                if new_status == 'Hoàn thành':
                    Ve.objects.filter(ChuyenXe_id=chuyenxe_id).update(
                        TrangThai='Đã đi', 
                        TrangThaiThanhToan='Đã thanh toán'
                    )
                messages.success(request, 'Cập nhật trạng thái thành công.')
            except Exception as e:
                messages.error(request, f'Lỗi cập nhật: {str(e)}')
    ve_list = Ve.objects.filter(ChuyenXe_id=chuyenxe_id).select_related('Ghe')
    
    user_auth = User_Authentication.objects.filter(UserID=user_id).first()
    taixe_obj = user_auth.Taixe if user_auth else None
    
    nha_xe_obj = None
    detail = CHITIETTAIXE.objects.filter(Taixe_id=taixe_obj.TaixeID if taixe_obj else None).first()
    if detail:
        nha_xe_obj = detail.Nhaxe
            
    return render(request, 'home/taixe_chitietchuyenxe.html', {
        'chuyen': chuyen,
        've_list': ve_list,
        'nha_xe': nha_xe_obj,
        'ten_taixe': taixe_obj.HoTen if taixe_obj else None,
        'avatar_url': getattr(taixe_obj, 'HinhAnhURL', None) if taixe_obj else None
    })

@nhaxe_required
def lotrinh(request):
    nha_xe_id = request.session.get('user_id')
    nha_xe_obj = None
    if nha_xe_id:
        try:
            nha_xe_obj = Nhaxe.objects.get(NhaxeID=nha_xe_id)
        except:
            pass

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
        've_list': ve_list,
        'nha_xe': nha_xe_obj
    })

@nhaxe_required
def chitietchuyenxe(request):
    if request.method == 'POST':
        post_id = request.POST.get('id')
        new_status = request.POST.get('status')
        if post_id and new_status:
            try:
                ChuyenXe.objects.filter(pk=post_id).update(TrangThai=new_status)
                # Tự động cập nhật vé thành 'Đã đi' nếu chuyến xe hoàn thành
                if new_status == 'Hoàn thành':
                    Ve.objects.filter(ChuyenXe_id=post_id).update(TrangThai='Đã đi', TrangThaiThanhToan='Đã thanh toán')
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
            overdue_trips_list = ChuyenXe.objects.filter(
                NgayKhoiHanh__lt=today,
                TrangThai='Chưa hoàn thành',
                TuyenXe__nhaXe_id=nha_xe_id
            ).select_related('TuyenXe')
            overdue_trips_count = overdue_trips_list.count()
        except Exception:
            pass

    return render(request, 'home/chitietchuyenxe.html', {
        'trip_json': json.dumps(trip_data),
        'chuyenxe_id': chuyenxe_id,
        'trip_status': cx.TrangThai or 'Chưa hoàn thành',
        'has_driver': cx.Taixe is not None,
        've_list': ve_list,
        'nha_xe': nha_xe_obj,
        'overdue_trips': overdue_trips_list if 'overdue_trips_list' in locals() else [],
        'overdue_trips_count': overdue_trips_count
    })
