from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import ChuyenXe, TuyenXe, Xe, Taixe
import random

# ==================== NHÀ XE (nx) ====================

def quanlychuyenxe(request):
    """
    Hiển thị danh sách chuyến xe sử dụng Django ORM kết nối Supabase.
    """
    # Lấy toàn bộ chuyến xe, tối ưu JOIN với Tuyến và Xe
    trips = ChuyenXe.objects.select_related('TuyenXe', 'Xe', 'Taixe').all()
    
    chuyen_xe_list = []
    for cx in trips:
        # Map dữ liệu để tương thích với template hiện tại
        data = {
            'ChuyenXeID': cx.ChuyenXeID,
            'route_name': cx.TuyenXe.tenTuyen if cx.TuyenXe else '-',
            'gio_di_fmt': cx.GioDi.strftime('%H:%M') if cx.GioDi else '-',
            'NgayKhoiHanh': cx.NgayKhoiHanh,
            'TrangThai': cx.TrangThai or 'Đang chờ',
            'seat_count': cx.Xe.SoGhe if cx.Xe else '-',
            'Xe': cx.Xe.XeID if cx.Xe else None,
            'Taixe': cx.Taixe.TaixeID if cx.Taixe else None,
            'TuyenXe': cx.TuyenXe.tuyenXeID if cx.TuyenXe else None,
        }
        chuyen_xe_list.append(data)
        
    return render(request, 'home/quanlychuyenxe.html', {'chuyen_xe_list': chuyen_xe_list})

def themchuyenxe(request):
    """
    Thêm chuyến xe mới trực tiếp vào database Supabase.
    """
    if request.method == 'POST':
        try:
            # Tạo ID mới ngẫu nhiên (VD: CX12345)
            new_id = "CX" + str(random.randint(10000, 99999))
            
            # Lấy các instance từ ID
            tuyen_inst = get_object_or_404(TuyenXe, pk=request.POST.get('tuyenxe'))
            xe_inst = get_object_or_404(Xe, pk=request.POST.get('xe'))
            taixe_inst = get_object_or_404(Taixe, pk=request.POST.get('taixe'))
            
            ChuyenXe.objects.create(
                ChuyenXeID=new_id,
                TuyenXe=tuyen_inst,
                Xe=xe_inst,
                Taixe=taixe_inst,
                NgayKhoiHanh=request.POST.get('date'),
                GioDi=request.POST.get('time'),
                TrangThai='Đang chờ'
            )
            messages.success(request, 'Thêm chuyến xe thành công.')
        except Exception as e:
            messages.error(request, f'Lỗi khi thêm chuyến xe: {str(e)}')

    # Load options cho dropdown
    tuyen_xe_list = TuyenXe.objects.all()
    xe_list = Xe.objects.all()
    taixe_list = Taixe.objects.all()
    
    return render(request, 'home/themchuyenxe.html', {
        'tuyen_xe_list': tuyen_xe_list,
        'xe_list': xe_list,
        'taixe_list': taixe_list
    })

def suachuyenxe(request):
    """
    Chỉnh sửa thông tin chuyến xe qua ORM.
    """
    chuyenxe_id = request.POST.get('id') or request.GET.get('id')
    chuyen = get_object_or_404(ChuyenXe, pk=chuyenxe_id)

    if request.method == 'POST':
        try:
            chuyen.TuyenXe = get_object_or_404(TuyenXe, pk=request.POST.get('tuyenxe'))
            chuyen.Xe = get_object_or_404(Xe, pk=request.POST.get('xe'))
            chuyen.Taixe = get_object_or_404(Taixe, pk=request.POST.get('taixe'))
            chuyen.NgayKhoiHanh = request.POST.get('date')
            chuyen.GioDi = request.POST.get('time')
            chuyen.save()
            messages.success(request, 'Sửa chuyến xe thành công.')
            return redirect('quanlychuyenxe')
        except Exception as e:
            messages.error(request, f'Lỗi khi cập nhật: {str(e)}')

    return render(request, 'home/suachuyenxe.html', {
        'chuyen': chuyen,
        'tuyen_xe_list': TuyenXe.objects.all(),
        'xe_list': Xe.objects.all(),
        'taixe_list': Taixe.objects.all()
    })

def hoanthanh_chuyenxe(request, pk):
    """Cập nhật trạng thái chuyến xe thành 'Hoàn thành'."""
    if request.method == 'POST':
        try:
            ChuyenXe.objects.filter(pk=pk).update(TrangThai='Hoàn thành')
            messages.success(request, 'Đã cập nhật trạng thái: Hoàn thành.')
        except Exception as e:
            messages.error(request, f'Lỗi: {str(e)}')
    return redirect('quanlychuyenxe')

# ==================== TÀI XẾ (tx) ====================

def taixe_quanlychuyenxe(request):
    """Danh sách chuyến xe của riêng tài xế đang đăng nhập."""
    user_id = request.session.get('user_id')
    chuyen_xe_list = []
    if user_id:
        # Lọc chuyến xe theo TaixeID
        chuyen_xe_list = ChuyenXe.objects.filter(Taixe__TaixeID=user_id).select_related('TuyenXe', 'Xe')
        
    return render(request, 'home/taixe_quanlychuyenxe.html', {'chuyen_xe_list': chuyen_xe_list})

def taixe_chitietchuyenxe(request):
    """Chi tiết chuyến xe cho tài xế."""
    chuyenxe_id = request.POST.get('id') or request.GET.get('id')
    if not chuyenxe_id:
        return redirect('taixe_quanlychuyenxe')
        
    chuyen = get_object_or_404(ChuyenXe, pk=chuyenxe_id)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status:
            chuyen.TrangThai = new_status
            chuyen.save()
            messages.success(request, 'Cập nhật trạng thái thành công.')
            return redirect(f"/taixe_chitietchuyenxe?id={chuyenxe_id}")
            
    return render(request, 'home/taixe_chitietchuyenxe.html', {'chuyen': chuyen})
