from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from .models import DanhGia, ChuyenXe, KhachHang, Ve, Nhaxe
from datetime import timedelta
import re
from .decorators import nhaxe_required as yeu_cau_nha_xe

def danh_gia_chuyen_xe(request, tab=None):
    """Lấy danh sách các chuyến xe khách hàng đã đi để thực hiện đánh giá."""
    ma_khach_hang = request.session.get('user_id')
    if not ma_khach_hang:
        return redirect('dangnhap')

    # Xác định tab đang được chọn (Chờ đánh giá hoặc Đã đánh giá)
    tab_hien_tai = request.GET.get('tab', tab) if request.GET.get('tab') else tab

    thoi_gian_hien_tai = timezone.now()
    han_3_ngay = thoi_gian_hien_tai - timedelta(days=3)

    # 1. Lấy danh sách vé chưa thực hiện đánh giá
    ve_da_danh_gia_ids = DanhGia.objects.filter(KhachHang_id=ma_khach_hang).values_list('Ve_id', flat=True)
    
    danh_sach_ve_cho = Ve.objects.filter(
        KhachHang_id=ma_khach_hang,
        TrangThai='Đã đi'
    ).exclude(VeID__in=ve_da_danh_gia_ids).select_related('ChuyenXe__TuyenXe__nhaXe').defer('ChuyenXe__TuyenXe__nhaXe__AnhDaiDienURL')
    
    chuyen_xe_cho_danh_gia = []
    for ve in danh_sach_ve_cho:
        chuyen_xe_cho_danh_gia.append({'chuyen': ve.ChuyenXe, 've': ve})

    # 2. Lấy danh sách các đánh giá đã thực hiện
    danh_sach_da_danh_gia = DanhGia.objects.filter(
        KhachHang_id=ma_khach_hang
    ).select_related('Nhaxe').defer('Nhaxe__AnhDaiDienURL').order_by('-NgayDanhGia')
    
    for dg in danh_sach_da_danh_gia:
        try:
            dg.TenNhaxe_Display = dg.Nhaxe.TenNhaXe if dg.Nhaxe.TenNhaXe else dg.Nhaxe.NhaxeID
        except:
            dg.TenNhaxe_Display = "Nhà xe"
            
        # Kiểm tra điều kiện chỉnh sửa (trong vòng 3 ngày)
        dg.co_the_sua = dg.NgayDanhGia >= han_3_ngay

    return render(request, 'khachhang/danhgiachuyenxe.html', {
        'chuyen_xe_cho_danh_gia': chuyen_xe_cho_danh_gia,
        'danh_sach_da_danh_gia': danh_sach_da_danh_gia,
        'active_tab': tab_hien_tai
    })

def viet_moi_danh_gia(request, ve_id):
    """Hiển thị giao diện viết hoặc chỉnh sửa đánh giá."""
    ma_khach_hang = request.session.get('user_id')
    if not ma_khach_hang:
        messages.error(request, "Vui lòng đăng nhập để thực hiện chức năng này.")
        return redirect('dangnhap')

    ve_doi_tuong = get_object_or_404(
        Ve.objects.select_related('ChuyenXe__TuyenXe__nhaXe').defer('ChuyenXe__TuyenXe__nhaXe__AnhDaiDienURL'), 
        pk=ve_id, 
        KhachHang_id=ma_khach_hang
    )
    
    danh_gia_cu = DanhGia.objects.filter(Ve_id=ve_id, KhachHang_id=ma_khach_hang).first()
    
    if danh_gia_cu:
        if danh_gia_cu.NgayDanhGia < timezone.now() - timedelta(days=3):
            messages.error(request, "Đã quá hạn 3 ngày, bạn không thể sửa đánh giá này.")
            return redirect('danhgiachuyenxe')

    nha_xe_doi_tuong = ve_doi_tuong.ChuyenXe.TuyenXe.nhaXe
    return render(request, 'khachhang/vietdanhgia.html', {
        've': ve_doi_tuong,
        'chuyen': ve_doi_tuong.ChuyenXe,
        'nhaxe': nha_xe_doi_tuong,
        'danh_gia_cu': danh_gia_cu
    })

def luu_danh_gia_he_thong(request):
    """Xử lý lưu mới hoặc cập nhật đánh giá vào cơ sở dữ liệu."""
    if request.method == 'POST':
        ma_khach_hang = request.session.get('user_id')
        if not ma_khach_hang:
            messages.error(request, "Vui lòng đăng nhập để thực hiện.")
            return redirect('dangnhap')

        ma_ve = request.POST.get('ve_id')
        ma_nha_xe = request.POST.get('nhaxe_id')
        diem_so = int(request.POST.get('diem_so'))
        noi_dung_nhan_xet = request.POST.get('nhan_xet')
        che_do_an_danh = request.POST.get('an_danh') == 'on'

        ve_doi_tuong = get_object_or_404(Ve, pk=ma_ve, KhachHang_id=ma_khach_hang)
        danh_gia_ton_tai = DanhGia.objects.filter(Ve_id=ma_ve, KhachHang_id=ma_khach_hang).first()

        try:
            nha_xe_doi_tuong = Nhaxe.objects.defer('AnhDaiDienURL').get(NhaxeID=ma_nha_xe)
            if nha_xe_doi_tuong.SoLuotDanhGia is None: nha_xe_doi_tuong.SoLuotDanhGia = 0
            if nha_xe_doi_tuong.TongDiemDanhGia is None: nha_xe_doi_tuong.TongDiemDanhGia = 0

            if danh_gia_ton_tai:
                # Kiểm tra hạn sửa đổi
                if danh_gia_ton_tai.NgayDanhGia < timezone.now() - timedelta(days=3):
                    messages.error(request, "Đã quá hạn chỉnh sửa.")
                    return redirect('danhgiachuyenxe')

                # Cập nhật tổng điểm của nhà xe
                nha_xe_doi_tuong.TongDiemDanhGia = nha_xe_doi_tuong.TongDiemDanhGia - danh_gia_ton_tai.Diemso + diem_so
                
                danh_gia_ton_tai.Diemso = diem_so
                danh_gia_ton_tai.Nhanxet = noi_dung_nhan_xet
                danh_gia_ton_tai.AnDanh = che_do_an_danh
                danh_gia_ton_tai.NgayDanhGia = timezone.now()
                danh_gia_ton_tai.save()
                nha_xe_doi_tuong.save()
                messages.success(request, "Cập nhật đánh giá thành công!")
            else:
                # Tạo mã đánh giá mới (DG0001...)
                danh_gia_cu_nhat = DanhGia.objects.all().order_by('DanhGiaID').last()
                so_tiep_theo = 1
                if danh_gia_cu_nhat:
                    ket_qua_khop = re.search(r'\d+', danh_gia_cu_nhat.DanhGiaID)
                    if ket_qua_khop: so_tiep_theo = int(ket_qua_khop.group()) + 1
                ma_danh_gia_moi = f"DG{so_tiep_theo:04d}"

                DanhGia.objects.create(
                    DanhGiaID=ma_danh_gia_moi, Nhaxe_id=ma_nha_xe, KhachHang_id=ma_khach_hang,
                    Ve_id=ma_ve, Diemso=diem_so, Nhanxet=noi_dung_nhan_xet,
                    AnDanh=che_do_an_danh, NgayDanhGia=timezone.now()
                )
                nha_xe_doi_tuong.SoLuotDanhGia += 1
                nha_xe_doi_tuong.TongDiemDanhGia += diem_so
                nha_xe_doi_tuong.save()
                messages.success(request, "Đánh giá của bạn đã được ghi nhận!")

            return redirect('dadanhgia')
        except Exception as loi:
            messages.error(request, f"Lỗi: {loi}")
            return redirect('danhgiachuyenxe')

    return redirect('danh_gia_chuyen_xe')

@yeu_cau_nha_xe
def nha_xe_xem_tat_ca_danh_gia(request):
    """Dành cho Nhà xe xem và thống kê các đánh giá từ khách hàng."""
    ma_nha_xe = request.session.get('user_id')
    nha_xe_doi_tuong = get_object_or_404(Nhaxe.objects.defer('AnhDaiDienURL'), NhaxeID=ma_nha_xe)
    
    danh_sach_dg = DanhGia.objects.filter(Nhaxe=nha_xe_doi_tuong).select_related('KhachHang', 'Ve__ChuyenXe__TuyenXe').order_by('-NgayDanhGia')
    
    from django.db.models import Avg, Count
    thong_ke = danh_sach_dg.aggregate(
        tong_dg=Count('DanhGiaID'),
        diem_tb=Avg('Diemso')
    )
    
    so_luong_sao = {i: danh_sach_dg.filter(Diemso=i).count() for i in range(1, 6)}
    
    phan_tram_sao = {}
    tong_so = thong_ke['tong_dg'] or 1
    for i in range(1, 6):
        phan_tram_sao[i] = (so_luong_sao[i] / tong_so) * 100

    return render(request, 'nhaxe/xem_danh_gia.html', {
        'nhaxe': nha_xe_doi_tuong,
        'danh_sach_dg': danh_sach_dg,
        'stats': thong_ke,
        'sao_counts': so_luong_sao,
        'sao_percent': phan_tram_sao
    })
