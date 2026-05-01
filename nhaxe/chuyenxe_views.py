from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import ChuyenXe, TuyenXe, Xe, Taixe, Nhaxe, User_Authentication, Ve, GheNgoi
from datetime import datetime
import random



# ==================== NHÀ XE (nx) ====================

def quanlychuyenxe(request):
    nha_xe_id = request.session.get('user_id')
    if not nha_xe_id:
        return redirect('index')

    try:
        from django.db.models import Count
        nha_xe_obj = get_object_or_404(Nhaxe, NhaxeID=nha_xe_id)
        
        # Thông báo chuyến trễ
        today = datetime.now().date()
        # WORKAROUND cho TuyenXe_id (như đã sửa ở views.py)
        overdue_trips = ChuyenXe.objects.filter(
            NgayKhoiHanh__lt=today,
            TrangThai='Chưa hoàn thành'
        ).select_related('TuyenXe')
        
        overdue_trips_list = [trip for trip in overdue_trips if trip.TuyenXe and getattr(trip.TuyenXe, 'nhaXe_id', getattr(trip.TuyenXe, 'nhaxe_id', None)) == nha_xe_id]
        overdue_trips_count = len(overdue_trips_list)

        # Lọc chuyến xe thuộc nhà xe này
        # WORKAROUND cho TuyenXe_id
        trips_raw = ChuyenXe.objects.all().select_related('TuyenXe', 'Xe', 'Taixe').order_by('-NgayKhoiHanh', '-GioDi')
        trips = [trip for trip in trips_raw if trip.TuyenXe and getattr(trip.TuyenXe, 'nhaXe_id', getattr(trip.TuyenXe, 'nhaxe_id', None)) == nha_xe_id]
        
        chuyen_xe_list = []
        for cx in trips:
            total_seats = cx.Xe.Loaixe.SoCho if cx.Xe and cx.Xe.Loaixe else 0
            ticket_count = Ve.objects.filter(ChuyenXe=cx).count()
            chuyen_xe_list.append({
                'ChuyenXeID':   cx.ChuyenXeID,
                'route_name':   cx.TuyenXe.tenTuyen if cx.TuyenXe else '-',
                'gio_di_fmt':   cx.GioDi.strftime('%H:%M') if cx.GioDi else '-',
                'NgayKhoiHanh': cx.NgayKhoiHanh,
                'TrangThai':    cx.TrangThai or 'Chưa hoàn thành',
                'seat_count':   total_seats,
                'available_seats': (total_seats - ticket_count) if total_seats > 0 else 0,
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
        return render(request, 'home/quanlychuyenxe.html', {'chuyen_xe_list': []})

def themchuyenxe(request):
    nha_xe_id = request.session.get('user_id')
    if not nha_xe_id:
        return redirect('index')
    
    nha_xe_obj = get_object_or_404(Nhaxe, NhaxeID=nha_xe_id)
    
    # Thông báo chuyến trễ
    today = datetime.now().date()
    overdue_trips_raw = ChuyenXe.objects.filter(
        NgayKhoiHanh__lt=today,
        TrangThai='Chưa hoàn thành'
    ).select_related('TuyenXe')
    
    overdue_trips_list = [trip for trip in overdue_trips_raw if trip.TuyenXe and getattr(trip.TuyenXe, 'nhaXe_id', getattr(trip.TuyenXe, 'nhaxe_id', None)) == nha_xe_id]
    overdue_trips_count = len(overdue_trips_list)
        
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

    # WORKAROUND cho TuyenXe_id
    tuyen_xe_list_raw = TuyenXe.objects.all()
    tuyen_xe_list = [tuyen for tuyen in tuyen_xe_list_raw if getattr(tuyen, 'nhaXe_id', getattr(tuyen, 'nhaxe_id', None)) == nha_xe_id]
    xe_list = Xe.objects.filter(Nhaxe_id=nha_xe_id)
    
    # WORKAROUND cho Nhaxe_id trong CHITIETTAIXE
    taixe_list_raw = Taixe.objects.all().prefetch_related('chitiettaixe_set')
    taixe_list = []
    for driver in taixe_list_raw:
        details = driver.chitiettaixe_set.all()
        for detail in details:
             if getattr(detail, 'Nhaxe_id', getattr(detail, 'nhaxe_id', None)) == nha_xe_id:
                  taixe_list.append(driver)
                  break
    
    return render(request, 'home/themchuyenxe.html', {
        'tuyen_xe_list': tuyen_xe_list,
        'xe_list': xe_list,
        'taixe_list': taixe_list,
        'nha_xe': nha_xe_obj,
        'avatar_url': getattr(nha_xe_obj, 'AnhDaiDienURL', None) if nha_xe_obj else None,
        'overdue_trips': overdue_trips_list,
        'overdue_trips_count': overdue_trips_count
    })

def suachuyenxe(request, pk):
    nha_xe_id = request.session.get('user_id')
    if not nha_xe_id:
        return redirect('index')

    nha_xe_obj = get_object_or_404(Nhaxe, NhaxeID=nha_xe_id)
    
    # Thông báo chuyến trễ
    today = datetime.now().date()
    overdue_trips_raw = ChuyenXe.objects.filter(
        NgayKhoiHanh__lt=today,
        TrangThai='Chưa hoàn thành'
    ).select_related('TuyenXe')
    
    overdue_trips_list = [trip for trip in overdue_trips_raw if trip.TuyenXe and getattr(trip.TuyenXe, 'nhaXe_id', getattr(trip.TuyenXe, 'nhaxe_id', None)) == nha_xe_id]
    overdue_trips_count = len(overdue_trips_list)

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
                    Ve.objects.filter(ChuyenXe_id=chuyen.ChuyenXeID).update(TrangThai='Đã đi')
            chuyen.save()
            messages.success(request, 'Sửa chuyến xe thành công.')
            return redirect('quanlychuyenxe')
        except Exception as e:
            messages.error(request, f'Lỗi khi cập nhật: {str(e)}')

    tuyen_xe_list_raw = TuyenXe.objects.all()
    tuyen_xe_list = [tuyen for tuyen in tuyen_xe_list_raw if getattr(tuyen, 'nhaXe_id', getattr(tuyen, 'nhaxe_id', None)) == nha_xe_id]
    xe_list = Xe.objects.filter(Nhaxe_id=nha_xe_id)
    
    # WORKAROUND cho Nhaxe_id trong CHITIETTAIXE
    taixe_list_raw = Taixe.objects.all().prefetch_related('chitiettaixe_set')
    taixe_list = []
    for driver in taixe_list_raw:
        details = driver.chitiettaixe_set.all()
        for detail in details:
             if getattr(detail, 'Nhaxe_id', getattr(detail, 'nhaxe_id', None)) == nha_xe_id:
                  taixe_list.append(driver)
                  break
    
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

def hoanthanh_chuyenxe(request, pk):
    """Cập nhật trạng thái chuyến xe thành 'Hoàn thành'."""
    if request.method == 'POST':
        try:
            ChuyenXe.objects.filter(pk=pk).update(TrangThai='Hoàn thành')
            Ve.objects.filter(ChuyenXe_id=pk).update(TrangThai='Đã đi')
            messages.success(request, 'Đã cập nhật trạng thái: Hoàn thành.')
        except Exception as e:
            messages.error(request, f'Lỗi: {str(e)}')
    return redirect(f"/chitietchuyenxe?id={pk}")

# ==================== TÀI XẾ (tx) ====================

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
                'ChuyenXeID': cx.ChuyenXeID,
                'TuyenXe': cx.TuyenXe,
                'GioDi': cx.GioDi,
                'Xe': cx.Xe,
                'TrangThai': cx.TrangThai,
                'seat_count': total_seats,
                'available_seats': (total_seats - cx.ticket_count) if total_seats > 0 else 0
            })
        return render(request, 'home/taixe_quanlychuyenxe.html', {
            'chuyen_xe_list': chuyen_xe_list,
            'nha_xe': nha_xe_obj,
            'ten_taixe': taixe_obj.HoTen if taixe_obj else None,
            'avatar_url': getattr(taixe_obj, 'HinhAnhURL', None) if taixe_obj else None
        })
    except Exception:
        return render(request, 'home/taixe_quanlychuyenxe.html', {
            'chuyen_xe_list': [],
            'nha_xe': None,
            'ten_taixe': request.session.get('username')
        })

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
