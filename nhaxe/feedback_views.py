from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from .models import DanhGia, ChuyenXe, KhachHang, Ve, Nhaxe
import uuid

from datetime import timedelta

def danhgiachuyenxe(request):
    """Lấy danh sách các chuyến xe khách hàng đã đi để đánh giá (Hạn 7 ngày)."""
    khach_hang_id = request.session.get('user_id')
    if not khach_hang_id:
        return redirect('dangnhap')

    bay_gio = timezone.now()
    han_7_ngay = bay_gio - timedelta(days=7)
    han_3_ngay = bay_gio - timedelta(days=3)

    # 1. Lấy vé CHƯA đánh giá và CHƯA quá 7 ngày kể từ ngày khởi hành
    ve_da_danh_gia_ids = DanhGia.objects.filter(KhachHang_id=khach_hang_id).values_list('Ve_id', flat=True)
    ve_cho_danh_gia = Ve.objects.filter(
        KhachHang_id=khach_hang_id,
        ChuyenXe__NgayKhoiHanh__gte=han_7_ngay.date() # Chỉ lấy vé trong vòng 7 ngày qua
    ).exclude(VeID__in=ve_da_danh_gia_ids)
    
    chuyen_xe_cho_danh_gia = []
    for ve in ve_cho_danh_gia:
        chuyen_xe_cho_danh_gia.append({'chuyen': ve.ChuyenXe, 've': ve})

    # 2. Lấy danh sách đã đánh giá và đánh dấu các bản được phép sửa (trong 3 ngày)
    danh_sach_da_danh_gia = DanhGia.objects.filter(KhachHang_id=khach_hang_id).select_related('Nhaxe', 'Ve').order_by('-NgayDanhGia')
    
    for dg in danh_sach_da_danh_gia:
        dg.TenNhaxe_Display = dg.Nhaxe.TenNhaXe if dg.Nhaxe.TenNhaXe else dg.Nhaxe.NhaxeID
        # Kiểm tra xem có nằm trong hạn 3 ngày để sửa không
        dg.is_editable = dg.NgayDanhGia >= han_3_ngay

    return render(request, 'khachhang/danhgiachuyenxe.html', {
        'chuyen_xe_cho_danh_gia': chuyen_xe_cho_danh_gia,
        'danh_sach_da_danh_gia': danh_sach_da_danh_gia
    })

def vietdanhgia(request, ve_id):
    """Hiển thị form đánh giá (Hỗ trợ cả Thêm mới và Sửa)."""
    khach_hang_id = request.session.get('user_id')
    ve = get_object_or_404(Ve, pk=ve_id)
    
    # Kiểm tra xem đã có đánh giá chưa
    danh_gia_cu = DanhGia.objects.filter(Ve_id=ve_id, KhachHang_id=khach_hang_id).first()
    
    # Nếu là sửa, kiểm tra hạn 3 ngày
    if danh_gia_cu:
        bay_gio = timezone.now()
        if danh_gia_cu.NgayDanhGia < bay_gio - timedelta(days=3):
            messages.error(request, "Đã quá hạn 3 ngày, bạn không thể sửa đánh giá này.")
            return redirect('danhgiachuyenxe')

    nhaxe = ve.ChuyenXe.TuyenXe.nhaXe
    return render(request, 'khachhang/vietdanhgia.html', {
        've': ve,
        'chuyen': ve.ChuyenXe,
        'nhaxe': nhaxe,
        'danh_gia_cu': danh_gia_cu # Truyền dữ liệu cũ vào form nếu có
    })

def submit_danhgia(request):
    """Lưu hoặc cập nhật đánh giá."""
    if request.method == 'POST':
        khach_hang_id = request.session.get('user_id')
        ve_id = request.POST.get('ve_id')
        nhaxe_id = request.POST.get('nhaxe_id')
        diem_so = int(request.POST.get('diem_so'))
        nhan_xet = request.POST.get('nhan_xet')
        an_danh = request.POST.get('an_danh') == 'on'

        danh_gia_exist = DanhGia.objects.filter(Ve_id=ve_id).first()

        try:
            nhaxe = Nhaxe.objects.get(NhaxeID=nhaxe_id)
            if nhaxe.SoLuotDanhGia is None: nhaxe.SoLuotDanhGia = 0
            if nhaxe.TongDiemDanhGia is None: nhaxe.TongDiemDanhGia = 0

            if danh_gia_exist:
                # KIỂM TRA HẠN SỬA (3 ngày)
                if danh_gia_exist.NgayDanhGia < timezone.now() - timedelta(days=3):
                    messages.error(request, "Đã quá hạn chỉnh sửa.")
                    return redirect('danhgiachuyenxe')

                # LOGIC CẬP NHẬT: Trừ điểm cũ, cộng điểm mới
                nhaxe.TongDiemDanhGia = nhaxe.TongDiemDanhGia - danh_gia_exist.Diemso + diem_so
                
                danh_gia_exist.Diemso = diem_so
                danh_gia_exist.Nhanxet = nhan_xet
                danh_gia_exist.AnDanh = an_danh
                danh_gia_exist.NgayDanhGia = timezone.now() # Cập nhật lại ngày sửa
                danh_gia_exist.save()
                nhaxe.save()
                messages.success(request, "Đã cập nhật đánh giá thành công!")
            else:
                # LOGIC THÊM MỚI
                last_dg = DanhGia.objects.all().order_by('DanhGiaID').last()
                num = 1
                if last_dg:
                    import re
                    match = re.search(r'\d+', last_dg.DanhGiaID)
                    if match: num = int(match.group()) + 1
                new_id = f"DG{num:04d}"

                DanhGia.objects.create(
                    DanhGiaID=new_id, Nhaxe_id=nhaxe_id, KhachHang_id=khach_hang_id,
                    Ve_id=ve_id, Diemso=diem_so, Nhanxet=nhan_xet,
                    AnDanh=an_danh, NgayDanhGia=timezone.now()
                )
                nhaxe.SoLuotDanhGia += 1
                nhaxe.TongDiemDanhGia += diem_so
                nhaxe.save()

            return redirect('/danhgiachuyenxe?tab=evaluated')
        except Exception as e:
            messages.error(request, f"Lỗi: {e}")
            return redirect('danhgiachuyenxe')

    return redirect('danhgiachuyenxe')
