from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import ChuyenXe, TuyenXe, Xe, Taixe, Nhaxe, User_Authentication
from datetime import datetime

# ==================== NHÀ XE (nx) ====================

def quanlychuyenxe(request):
    nha_xe_id = request.session.get('user_id')
    if not nha_xe_id:
        return redirect('index')

    try:
        # Lọc chuyến xe thuộc nhà xe này
        # (Chuyến xe -> Tuyến xe -> Nhà xe)
        chuyen_xe_list = ChuyenXe.objects.filter(TuyenXe__nhaXe_id=nha_xe_id).order_by('-NgayKhoiHanh', '-GioDi')
        return render(request, 'home/quanlychuyenxe.html', {'chuyen_xe_list': chuyen_xe_list})
    except Exception as e:
        messages.error(request, f'Lỗi lấy danh sách chuyến xe: {str(e)}')
        return render(request, 'home/quanlychuyenxe.html', {'chuyen_xe_list': []})

def themchuyenxe(request):
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
        except Exception as e:
            messages.error(request, f'Lỗi khi thêm chuyến xe: {str(e)}')

    # Dropdown options
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
    nha_xe_id = request.session.get('user_id')
    if not nha_xe_id:
        return redirect('index')

    if request.method == 'POST':
        chuyenxe_id = request.POST.get('id')
        try:
            ChuyenXe.objects.filter(ChuyenXeID=chuyenxe_id).update(
                TuyenXe_id=request.POST.get('tuyenxe'),
                Xe_id=request.POST.get('xe'),
                Taixe_id=request.POST.get('taixe'),
                NgayKhoiHanh=request.POST.get('date'),
                GioDi=request.POST.get('time')
            )
            messages.success(request, 'Sửa chuyến xe thành công.')
        except Exception as e:
            messages.error(request, f'Lỗi khi sửa: {str(e)}')
        return redirect('quanlychuyenxe')

    chuyenxe_id = request.GET.get('id')
    if not chuyenxe_id:
        return redirect('quanlychuyenxe')

    chuyen = get_object_or_404(ChuyenXe, ChuyenXeID=chuyenxe_id)
    tuyen_xe_list = TuyenXe.objects.filter(nhaXe_id=nha_xe_id)
    xe_list = Xe.objects.filter(Nhaxe_id=nha_xe_id)
    taixe_list = Taixe.objects.filter(chitiettaixe__Nhaxe_id=nha_xe_id)

    return render(request, 'home/suachuyenxe.html', {
        'chuyen': chuyen,
        'tuyen_xe_list': tuyen_xe_list,
        'xe_list': xe_list,
        'taixe_list': taixe_list
    })

# ==================== TÀI XẾ (tx) ====================

def taixe_quanlychuyenxe(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('index')

    try:
        # Chuyến xe của chính tài xế này
        chuyen_xe_list = ChuyenXe.objects.filter(Taixe_id=user_id).order_by('-NgayKhoiHanh', '-GioDi')
        return render(request, 'home/taixe_quanlychuyenxe.html', {'chuyen_xe_list': chuyen_xe_list})
    except Exception:
        return render(request, 'home/taixe_quanlychuyenxe.html', {'chuyen_xe_list': []})

def taixe_chitietchuyenxe(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('index')

    if request.method == 'POST':
        chuyenxe_id = request.POST.get('id')
        new_status = request.POST.get('status')
        if chuyenxe_id and new_status:
            try:
                ChuyenXe.objects.filter(ChuyenXeID=chuyenxe_id, Taixe_id=user_id).update(TrangThai=new_status)
                messages.success(request, 'Cập nhật trạng thái thành công.')
            except Exception as e:
                messages.error(request, f'Lỗi cập nhật: {str(e)}')
            return redirect(f"/taixe_chitietchuyenxe?id={chuyenxe_id}")
            
    chuyenxe_id = request.GET.get('id')
    if chuyenxe_id:
        chuyen = get_object_or_404(ChuyenXe, ChuyenXeID=chuyenxe_id, Taixe_id=user_id)
        return render(request, 'home/taixe_chitietchuyenxe.html', {'chuyen': chuyen})
            
    return redirect('taixe_quanlychuyenxe')
