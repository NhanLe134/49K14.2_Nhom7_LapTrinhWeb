from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import TuyenXe, Nhaxe, ChuyenXe
from datetime import datetime
from django.db import models
import requests
import json

# ==================== CÁC HÀM HỖ TRỢ TÍNH QUÃNG ĐƯỜNG ====================

def anh_xa_dia_diem_dac_biet(ten_dia_diem):
    """Bản đồ ánh xạ các tên điểm đặc biệt sang tọa độ Plus Code cụ thể."""
    ten_chuan_hoa = ten_dia_diem.strip().lower()
    if ten_chuan_hoa == 'huế':
        return 'FH7V+7Q Thuận Hóa, Huế, Việt Nam'
    elif ten_chuan_hoa == 'đà nẵng':
        return '36CJ+H3 An Hải, Đà Nẵng, Việt Nam'
    elif ten_chuan_hoa == 'hội an':
        return 'V8GG+7MR, An Hội, Hội An, Đà Nẵng, Việt Nam'
    return ten_dia_diem

def lay_toa_do_dia_ly(ten_dia_diem):
    """Lấy tọa độ từ Nominatim (OpenStreetMap) - Miễn phí."""
    if not ten_dia_diem:
        return None
    try:
        duong_dan = 'https://nominatim.openstreetmap.org/search'
        tham_so = {
            'q': f'{ten_dia_diem}, Việt Nam',
            'format': 'json',
            'limit': 1
        }
        tieu_de_gui = {'User-Agent': 'VexeApp/1.0'}
        phan_hoi = requests.get(duong_dan, params=tham_so, headers=tieu_de_gui)
        if phan_hoi.status_code == 200:
            du_lieu_json = phan_hoi.json()
            if du_lieu_json:
                return {'lat': du_lieu_json[0]['lat'], 'lon': du_lieu_json[0]['lon']}
    except Exception as loi:
        print(f'Lỗi lấy tọa độ: {loi}')
    return None

def tinh_quang_duong_thoi_gian_osrm(diem_di, diem_den, ds_trung_gian_chuoi=None):
    """Tính quãng đường và thời gian bằng OSRM (Open Source Routing Machine)."""
    try:
        toa_do_di = lay_toa_do_dia_ly(diem_di)
        toa_do_den = lay_toa_do_dia_ly(diem_den)
        
        if not toa_do_di or not toa_do_den:
            return None, None

        danh_sach_toa_do = [f'{toa_do_di["lon"]},{toa_do_di["lat"]}']
        
        if ds_trung_gian_chuoi:
            cac_diem_tg = [p.strip() for p in ds_trung_gian_chuoi.split(',') if p.strip()]
            for p in cac_diem_tg:
                toa_do_tg = lay_toa_do_dia_ly(p)
                if toa_do_tg:
                    danh_sach_toa_do.append(f'{toa_do_tg["lon"]},{toa_do_tg["lat"]}')
        
        danh_sach_toa_do.append(f'{toa_do_den["lon"]},{toa_do_den["lat"]}')
        chuoi_toa_do_duong_di = ';'.join(danh_sach_toa_do)

        duong_dan_api = f'https://router.project-osrm.org/route/v1/driving/{chuoi_toa_do_duong_di}?overview=false'
        phan_hoi = requests.get(duong_dan_api)
        if phan_hoi.status_code == 200:
            du_lieu_tra_ve = phan_hoi.json()
            if du_lieu_tra_ve.get('code') == 'Ok' and du_lieu_tra_ve.get('routes'):
                quang_duong_met = du_lieu_tra_ve['routes'][0]['distance']
                thoi_gian_giay = du_lieu_tra_ve['routes'][0]['duration']
                # Nhân đôi thời gian dự kiến để phù hợp thực tế đường xá Việt Nam
                thoi_gian_gio = (thoi_gian_giay / 3600.0) * 2
                return round(quang_duong_met / 1000.0, 1), round(thoi_gian_gio, 1)
    except Exception as loi:
        print(f'Lỗi OSRM: {loi}')
    return None, None

# ==================== CÁC VIEW QUẢN LÝ TUYẾN XE ====================

def quan_ly_tuyen_xe(request):
    """Hiển thị danh sách tuyến xe của nhà xe đang đăng nhập."""
    ma_nha_xe = request.session.get('user_id')
    if not ma_nha_xe:
        messages.error(request, 'Vui lòng đăng nhập để xem quản lý tuyến xe.')
        return redirect('dangnhap')

    nha_xe_doi_tuong = get_object_or_404(Nhaxe, NhaxeID=ma_nha_xe)

    # Lấy các chuyến xe bị quá hạn (trễ)
    ngay_hom_nay = datetime.now().date()
    cac_chuyen_xe_qua_han = ChuyenXe.objects.filter(
        NgayKhoiHanh__lt=ngay_hom_nay,
        TrangThai='Chưa hoàn thành'
    ).select_related('TuyenXe')
    
    danh_sach_chuyen_qua_han = [chuyen for chuyen in cac_chuyen_xe_qua_han if chuyen.TuyenXe and getattr(chuyen.TuyenXe, 'nhaXe_id', None) == ma_nha_xe]
    so_luong_chuyen_qua_han = len(danh_sach_chuyen_qua_han)

    # Lấy danh sách tuyến xe
    danh_sach_tuyen_xe = TuyenXe.objects.filter(nhaXe=nha_xe_doi_tuong)

    # Tổng hợp dữ liệu hiển thị cho từng tuyến
    du_lieu_tuyen_xe = []
    for tuyen in danh_sach_tuyen_xe:
        so_chuyen_dang_chay = ChuyenXe.objects.filter(
            TuyenXe=tuyen,
            TrangThai__in=['Chưa hoàn thành', 'Đang chạy']
        ).count()
        
        du_lieu_tuyen_xe.append({
            'tuyenXeID': tuyen.tuyenXeID,
            'tenTuyen': tuyen.tenTuyen,
            'diemDi': tuyen.diemDi,
            'diemDen': tuyen.diemDen,
            'QuangDuong': tuyen.QuangDuong,
            'ThoiGian': tuyen.ThoiGian,
            'so_chuyen': so_chuyen_dang_chay
        })

    return render(request, 'nhaxe/quanlytuyenxe.html', {
        'danh_sach_tuyen': du_lieu_tuyen_xe,
        'nha_xe': nha_xe_doi_tuong,
        'avatar_url': getattr(nha_xe_doi_tuong, 'AnhDaiDienURL', None),
        'overdue_trips': danh_sach_chuyen_qua_han,
        'overdue_trips_count': so_luong_chuyen_qua_han
    })

def them_moi_tuyen_xe(request):
    """Hiển thị form và xử lý thêm tuyến xe mới."""
    ma_nha_xe = request.session.get('user_id')
    if not ma_nha_xe:
        messages.error(request, 'Vui lòng đăng nhập để thêm tuyến xe.')
        return redirect('dangnhap')

    if request.method == 'POST':
        ten_tuyen = request.POST.get('tenTuyen')
        diem_di = request.POST.get('diemDi')
        diem_den = request.POST.get('diemDen')
        quang_duong = request.POST.get('quangDuong')
        diem_trung_gian = request.POST.get('diemTrungGian')
        thoi_gian = request.POST.get('thoiGian')

        # Tự động tính toán nếu để trống quãng đường hoặc thời gian
        if not quang_duong or not quang_duong.strip() or not thoi_gian or not thoi_gian.strip():
            kq_quang_duong, kq_thoi_gian = tinh_quang_duong_thoi_gian_osrm(diem_di, diem_den, diem_trung_gian)
            if not quang_duong or not quang_duong.strip():
                quang_duong = kq_quang_duong
            if not thoi_gian or not thoi_gian.strip():
                thoi_gian = kq_thoi_gian

        try:
            nha_xe_doi_tuong = Nhaxe.objects.get(NhaxeID=ma_nha_xe)
            
            # Tạo mã tuyến xe mới (TX0001...)
            tuyen_cu_nhat = TuyenXe.objects.all().order_by('tuyenXeID').last()
            so_lon_nhat = 0
            if tuyen_cu_nhat and tuyen_cu_nhat.tuyenXeID.startswith('TX'):
                 so_lon_nhat = int(tuyen_cu_nhat.tuyenXeID[2:])
            ma_moi = f'TX{so_lon_nhat + 1:04d}'

            TuyenXe.objects.create(
                tuyenXeID=ma_moi,
                tenTuyen=ten_tuyen,
                diemDi=diem_di,
                diemDen=diem_den,
                QuangDuong=quang_duong if quang_duong else None,
                DiemTrungGian=diem_trung_gian if diem_trung_gian else None,
                ThoiGian=thoi_gian if thoi_gian else None,
                nhaXe=nha_xe_doi_tuong
            )
            messages.success(request, 'Thêm tuyến xe thành công')
            return redirect('quanlytuyenxe')
        except Exception as loi:
            messages.error(request, f'Lỗi hệ thống: {loi}')
            return redirect('them_tuyen_xe')
            
    return render(request, 'nhaxe/form_tuyen_xe.html', {
        'tieu_de_form': 'Thêm tuyến mới',
        'tuyen': {},
        'nha_xe': Nhaxe.objects.filter(NhaxeID=ma_nha_xe).first()
    })

def cap_nhat_tuyen_xe(request, pk):
    """Xử lý chỉnh sửa thông tin tuyến xe."""
    ma_nha_xe = request.session.get('user_id')
    if not ma_nha_xe:
        messages.error(request, 'Vui lòng đăng nhập để sửa tuyến xe.')
        return redirect('dangnhap')

    tuyen_xe_doi_tuong = get_object_or_404(TuyenXe, pk=pk)
    
    # Kiểm tra quyền sở hữu
    if tuyen_xe_doi_tuong.nhaXe_id != ma_nha_xe:
        messages.error(request, 'Bạn không có quyền sửa tuyến xe này.')
        return redirect('quanlytuyenxe')

    if request.method == 'POST':
        ten_tuyen = request.POST.get('tenTuyen')
        diem_di = request.POST.get('diemDi')
        diem_den = request.POST.get('diemDen')
        quang_duong = request.POST.get('quangDuong')
        diem_trung_gian = request.POST.get('diemTrungGian')
        thoi_gian = request.POST.get('thoiGian')

        if not quang_duong or not quang_duong.strip() or not thoi_gian or not thoi_gian.strip():
            kq_quang_duong, kq_thoi_gian = tinh_quang_duong_thoi_gian_osrm(diem_di, diem_den, diem_trung_gian)
            if not quang_duong or not quang_duong.strip():
                quang_duong = kq_quang_duong
            if not thoi_gian or not thoi_gian.strip():
                thoi_gian = kq_thoi_gian

        try:
            tuyen_xe_doi_tuong.tenTuyen = ten_tuyen
            tuyen_xe_doi_tuong.diemDi = diem_di
            tuyen_xe_doi_tuong.diemDen = diem_den
            tuyen_xe_doi_tuong.QuangDuong = quang_duong if quang_duong else None
            tuyen_xe_doi_tuong.DiemTrungGian = diem_trung_gian if diem_trung_gian else None
            tuyen_xe_doi_tuong.ThoiGian = thoi_gian if thoi_gian else None
            tuyen_xe_doi_tuong.save()
            
            messages.success(request, 'Cập nhật tuyến xe thành công')
            return redirect('quanlytuyenxe')
        except Exception as loi:
            messages.error(request, f'Lỗi hệ thống: {loi}')
            
    return render(request, 'nhaxe/form_tuyen_xe.html', {
        'tieu_de_form': 'Chỉnh sửa tuyến',
        'tuyen': tuyen_xe_doi_tuong,
        'nha_xe': Nhaxe.objects.filter(NhaxeID=ma_nha_xe).first()
    })

def xoa_bo_tuyen_xe(request, pk):
    """Xử lý xóa tuyến xe ra khỏi hệ thống."""
    ma_nha_xe = request.session.get('user_id')
    if not ma_nha_xe:
        return redirect('dangnhap')

    if request.method in ['POST', 'GET']:
        tuyen_xe_doi_tuong = get_object_or_404(TuyenXe, pk=pk)
        
        if tuyen_xe_doi_tuong.nhaXe_id != ma_nha_xe:
            messages.error(request, 'Bạn không có quyền xóa tuyến xe này')
            return redirect('quanlytuyenxe')

        # Kiểm tra xem tuyến có đang được khai thác không
        co_chuyen_dang_chay = ChuyenXe.objects.filter(TuyenXe_id=pk).exists()

        if co_chuyen_dang_chay:
            messages.error(request, 'Không thể xóa tuyến xe này vì đang có chuyến xe chạy trên tuyến.')
            return redirect('quanlytuyenxe')

        try:
            ten_tuyen_xoa = tuyen_xe_doi_tuong.tenTuyen
            tuyen_xe_doi_tuong.delete()
            messages.success(request, f"Đã xóa tuyến '{ten_tuyen_xoa}' thành công.")
        except Exception as loi:
            messages.error(request, f'Lỗi hệ thống khi xóa: {loi}')
            
    return redirect('quanlytuyenxe')
