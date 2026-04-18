from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import ChuyenXe, TuyenXe, Xe, Taixe, Nhaxe, User_Authentication, Ve
from datetime import datetime
import random

# ==================== NHÀ XE (nx) ====================

def quanlychuyenxe(request):
    """
    Hiển thị danh sách chuyến xe thuộc nhà xe đang đăng nhập.
    """
    nha_xe_id = request.session.get('user_id')
    if not nha_xe_id:
        return redirect('index')

    try:
        # Lấy bản ghi chuyến xe và tối ưu JOIN với Tuyến và Xe
        # Lọc chuyến xe thuộc nhà xe này (Chuyến xe -> Tuyến xe -> Nhà xe)
        trips = ChuyenXe.objects.filter(TuyenXe__nhaXe_id=nha_xe_id)\
                                .select_related('TuyenXe', 'Xe', 'Taixe')\
                                .order_by('-NgayKhoiHanh', '-GioDi')
        
        chuyen_xe_list = []
        for cx in trips:
            # Map dữ liệu để tương thích với template
            data = {
                'ChuyenXeID':   cx.ChuyenXeID,
                'route_name':   cx.TuyenXe.tenTuyen if cx.TuyenXe else '-',
                'gio_di_fmt':   cx.GioDi.strftime('%H:%M') if cx.GioDi else '-',
                'NgayKhoiHanh': cx.NgayKhoiHanh,
                'TrangThai':    cx.TrangThai or 'Đang chờ',
                'seat_count':   cx.Xe.SoGhe if cx.Xe else '-',
                'Xe':           cx.Xe.XeID if cx.Xe else None,
                'Taixe':        cx.Taixe.TaixeID if cx.Taixe else None,
                'TuyenXe':      cx.TuyenXe.tuyenXeID if cx.TuyenXe else None,
            }
            chuyen_xe_list.append(data)

        return render(request, 'home/quanlychuyenxe.html', {'chuyen_xe_list': chuyen_xe_list})
    except Exception as e:
        messages.error(request, f'Lỗi lấy danh sách chuyến xe: {str(e)}')
        return render(request, 'home/quanlychuyenxe.html', {'chuyen_xe_list': []})

def themchuyenxe(request):
    """
    Thêm chuyến xe mới trực tiếp vào database Supabase (theo mã nhà xe).
    """
    nha_xe_id = request.session.get('user_id')
    if not nha_xe_id:
        return redirect('index')
        
    if request.method == 'POST':
        tuyen_id = request.POST.get('tuyenxe')
        xe_id = request.POST.get('xe')
        taixe_id = request.POST.get('taixe')
        ngay = request.POST.get('date')
        gio = request.POST.get('time')
        
        try:
            # 1. Tính ID mới (CX0001)
            all_ids = ChuyenXe.objects.values_list('ChuyenXeID', flat=True)
            max_num = 0
            for cx_id in all_ids:
                if cx_id and cx_id.startswith('CX') and cx_id[2:].isdigit():
                    num = int(cx_id[2:])
                    if num > max_num: max_num = num
            new_id = f"CX{max_num + 1:04d}"

            # 2. Tạo bản ghi
            ChuyenXe.objects.create(
                ChuyenXeID=new_id,
                TuyenXe_id=tuyen_id,
                Xe_id=xe_id,
                Taixe_id=taixe_id,
                NgayKhoiHanh=ngay,
                GioDi=gio,
                TrangThai='Đang chờ'
            )
            messages.success(request, 'Thêm chuyến xe thành công.')
            return redirect('quanlychuyenxe')
        except Exception as e:
            messages.error(request, f'Lỗi khi thêm chuyến xe: {str(e)}')

    # Dropdown options lọc theo nhà xe
    tuyen_xe_list = TuyenXe.objects.filter(nhaXe_id=nha_xe_id)
    xe_list = Xe.objects.filter(Nhaxe_id=nha_xe_id)
    # Lấy tài xế thuộc nhà xe này (qua CHITIETTAIXE)
    taixe_list = Taixe.objects.filter(chitiettaixe__Nhaxe_id=nha_xe_id)
    
    return render(request, 'home/themchuyenxe.html', {
        'tuyen_xe_list': tuyen_xe_list,
        'xe_list': xe_list,
        'taixe_list': taixe_list
    })

def suachuyenxe(request):
    """
    Chỉnh sửa thông tin chuyến xe qua ORM (lọc theo nhà xe).
    """
    nha_xe_id = request.session.get('user_id')
    if not nha_xe_id:
        return redirect('index')

    chuyenxe_id = request.POST.get('id') or request.GET.get('id')
    chuyen = get_object_or_404(ChuyenXe, ChuyenXeID=chuyenxe_id)

    if request.method == 'POST':
        try:
            chuyen.TuyenXe_id = request.POST.get('tuyenxe')
            chuyen.Xe_id = request.POST.get('xe')
            chuyen.Taixe_id = request.POST.get('taixe')
            chuyen.NgayKhoiHanh = request.POST.get('date')
            chuyen.GioDi = request.POST.get('time')
            chuyen.save()
            messages.success(request, 'Sửa chuyến xe thành công.')
            return redirect('quanlychuyenxe')
        except Exception as e:
            messages.error(request, f'Lỗi khi cập nhật: {str(e)}')

    return render(request, 'home/suachuyenxe.html', {
        'chuyen': chuyen,
        'tuyen_xe_list': TuyenXe.objects.filter(nhaXe_id=nha_xe_id),
        'xe_list': Xe.objects.filter(Nhaxe_id=nha_xe_id),
        'taixe_list': Taixe.objects.filter(chitiettaixe__Nhaxe_id=nha_xe_id)
    })

def hoanthanh_chuyenxe(request, pk):
    """Cập nhật trạng thái chuyến xe thành 'Hoàn thành'."""
    if request.method == 'POST':
        try:
            ChuyenXe.objects.filter(pk=pk).update(TrangThai='Hoàn thành')
            messages.success(request, 'Đã cập nhật trạng thái: Hoàn thành.')
        except Exception as e:
            messages.error(request, f'Lỗi: {str(e)}')
    return redirect(f"/chitietchuyenxe?id={pk}")

# ==================== TÀI XẾ (tx) ====================

def taixe_quanlychuyenxe(request):
    """Danh sách chuyến xe của riêng tài xế đang đăng nhập."""
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('index')

    try:
        # Chuyến xe của chính tài xế này
        chuyen_xe_list = ChuyenXe.objects.filter(Taixe_id=user_id).select_related('TuyenXe', 'Xe').order_by('-NgayKhoiHanh', '-GioDi')
        return render(request, 'home/taixe_quanlychuyenxe.html', {'chuyen_xe_list': chuyen_xe_list})
    except Exception:
        return render(request, 'home/taixe_quanlychuyenxe.html', {'chuyen_xe_list': []})

def taixe_chitietchuyenxe(request):
    """Chi tiết chuyến xe cho tài xế."""
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('index')
        
    chuyenxe_id = request.POST.get('id') or request.GET.get('id')
    if not chuyenxe_id:
        return redirect('taixe_quanlychuyenxe')

    # Đảm bảo chuyến xe này thuộc về tài xế đang đăng nhập
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
    # Lấy danh sách hành khách
    ve_list = Ve.objects.filter(ChuyenXe_id=chuyenxe_id).select_related('Ghe')
            
    return render(request, 'home/taixe_chitietchuyenxe.html', {
        'chuyen': chuyen,
        've_list': ve_list
    })
