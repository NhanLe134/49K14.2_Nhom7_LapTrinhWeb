from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import TuyenXe, Nhaxe, ChuyenXe
from datetime import datetime
from django.db import models
import requests
import json

# ==================== HELPER FUNCTIONS FOR DISTANCE CALCULATION ====================

def anh_xa_dia_diem(ten_dia_diem):
    '''Bản đồ ánh xạ các tên điểm đặc biệt sang tọa độ Plus Code cụ thể.'''
    ten_thap_len = ten_dia_diem.strip().lower()
    if ten_thap_len == 'huế':
        return 'FH7V+7Q Thuận Hóa, Huế, Việt Nam'
    elif ten_thap_len == 'đà nẵng':
        return '36CJ+H3 An Hải, Đà Nẵng, Việt Nam'
    elif ten_thap_len == 'hội an':
        return 'V8GG+7MR, An Hội, Hội An, Đà Nẵng, Việt Nam'
    return ten_dia_diem

def lay_toa_do(ten_dia_diem):
    '''Lấy tọa độ từ Nominatim (OpenStreetMap) - Miễn phí.'''
    if not ten_dia_diem:
        return None
    try:
        duong_dan = 'https://nominatim.openstreetmap.org/search'
        tham_so = {
            'q': f'{ten_dia_diem}, Việt Nam',
            'format': 'json',
            'limit': 1
        }
        tieu_de = {'User-Agent': 'VexeApp/1.0'}
        phan_hoi = requests.get(duong_dan, params=tham_so, headers=tieu_de)
        if phan_hoi.status_code == 200:
            du_lieu = phan_hoi.json()
            if du_lieu:
                return {'lat': du_lieu[0]['lat'], 'lon': du_lieu[0]['lon']}
    except Exception as e:
        print(f'Lỗi lấy tọa độ: {e}')
    return None

def tinh_quang_duong_osrm(diem_di, diem_den, ds_trung_gian_str=None):
    '''Tính quãng đường và thời gian bằng OSRM (Open Source Routing Machine) - Miễn phí.'''
    try:
        toa_do_di = lay_toa_do(diem_di)
        toa_do_den = lay_toa_do(diem_den)
        
        if not toa_do_di or not toa_do_den:
            return None, None

        danh_sach_toa_do = [f'{toa_do_di["lon"]},{toa_do_di["lat"]}']
        
        if ds_trung_gian_str:
            cac_diem_tg = [p.strip() for p in ds_trung_gian_str.split(',') if p.strip()]
            for p in cac_diem_tg:
                toa_do_tg = lay_toa_do(p)
                if toa_do_tg:
                    danh_sach_toa_do.append(f'{toa_do_tg["lon"]},{toa_do_tg["lat"]}')
        
        danh_sach_toa_do.append(f'{toa_do_den["lon"]},{toa_do_den["lat"]}')
        duong_di_toa_do = ';'.join(danh_sach_toa_do)

        duong_dan = f'https://router.project-osrm.org/route/v1/driving/{duong_di_toa_do}?overview=false'
        phan_hoi = requests.get(duong_dan)
        if phan_hoi.status_code == 200:
            du_lieu = phan_hoi.json()
            if du_lieu.get('code') == 'Ok' and du_lieu.get('routes'):
                quang_duong_met = du_lieu['routes'][0]['distance']
                thoi_gian_giay = du_lieu['routes'][0]['duration']
                # Nhân đôi thời gian dự kiến (vì phải đón trả khách và các yếu tố đường xá Việt Nam)
                thoi_gian_gio = (thoi_gian_giay / 3600.0) * 2
                return round(quang_duong_met / 1000.0, 1), round(thoi_gian_gio, 1)
    except Exception as e:
        print(f'Lỗi OSRM: {e}')
    return None, None

# ==================== TUYẾN XE VIEWS ====================

def quanlytuyenxe(request):
    '''
    Hiển thị danh sách tuyến xe của nhà xe
    '''
    nha_xe_id = request.session.get('user_id')
    if not nha_xe_id:
        messages.error(request, 'Vui lòng đăng nhập để xem quản lý tuyến xe.')
        return redirect('dangnhap')

    nha_xe_obj = get_object_or_404(Nhaxe, NhaxeID=nha_xe_id)

    # Thông báo chuyến trễ
    today = datetime.now().date()
    overdue_trips = ChuyenXe.objects.filter(
        NgayKhoiHanh__lt=today,
        TrangThai='Chưa hoàn thành'
    ).select_related('TuyenXe')
    
    overdue_trips_list = [trip for trip in overdue_trips if trip.TuyenXe and getattr(trip.TuyenXe, 'nhaXe_id', getattr(trip.TuyenXe, 'nhaxe_id', None)) == nha_xe_id]
    overdue_trips_count = len(overdue_trips_list)

    # Lấy danh sách tuyến trực tiếp từ DB
    danh_sach_tuyen_raw = TuyenXe.objects.filter(nhaXe=nha_xe_obj)

    # Tính toán số chuyến đang khai thác cho mỗi tuyến
    tuyen_data = []
    for tuyen in danh_sach_tuyen_raw:
        # Số chuyến đang hoạt động
        so_chuyen = ChuyenXe.objects.filter(
            TuyenXe=tuyen,
            TrangThai__in=['Chưa hoàn thành', 'Đang chạy']
        ).count()
        
        tuyen_data.append({
            'tuyenXeID': tuyen.tuyenXeID,
            'tenTuyen': tuyen.tenTuyen,
            'diemDi': tuyen.diemDi,
            'diemDen': tuyen.diemDen,
            'QuangDuong': tuyen.QuangDuong,
            'ThoiGian': tuyen.ThoiGian,
            'so_chuyen': so_chuyen
        })

    return render(request, 'nhaxe/quanlytuyenxe.html', {
        'danh_sach_tuyen': tuyen_data,
        'nha_xe': nha_xe_obj,
        'avatar_url': getattr(nha_xe_obj, 'AnhDaiDienURL', None) if nha_xe_obj else None,
        'overdue_trips': overdue_trips_list,
        'overdue_trips_count': overdue_trips_count
    })

def them_tuyen_xe(request):
    '''
    Hiển thị form và xử lý thêm tuyến xe mới với tính năng tự động tính quãng đường
    '''
    nha_xe_id = request.session.get('user_id')
    if not nha_xe_id:
        messages.error(request, 'Vui lòng đăng nhập để thêm tuyến xe.')
        return redirect('dangnhap')

    if request.method == 'POST':
        ten_tuyen = request.POST.get('tenTuyen')
        diem_di = request.POST.get('diemDi')
        diem_den = request.POST.get('diemDen')
        quang_duong = request.POST.get('quangDuong')
        diem_trung_gian = request.POST.get('diemTrungGian')
        thoi_gian = request.POST.get('thoiGian')

        # Nếu người dùng để trống quãng đường HOẶC thời gian, gọi OSRM để tính toán
        if not quang_duong or not quang_duong.strip() or not thoi_gian or not thoi_gian.strip():
            kq_quang_duong, kq_thoi_gian = tinh_quang_duong_osrm(diem_di, diem_den, diem_trung_gian)
            if not quang_duong or not quang_duong.strip():
                if kq_quang_duong is not None:
                    quang_duong = kq_quang_duong
            if not thoi_gian or not thoi_gian.strip():
                if kq_thoi_gian is not None:
                    thoi_gian = kq_thoi_gian

        try:
            nha_xe_obj = Nhaxe.objects.get(NhaxeID=nha_xe_id)
            
            # Tìm ID lớn nhất trong DB
            last_route = TuyenXe.objects.all().order_by('tuyenXeID').last()
            max_id = 0
            if last_route and last_route.tuyenXeID.startswith('TX'):
                 max_id = int(last_route.tuyenXeID[2:])
            id_moi = f'TX{max_id + 1:04d}'

            TuyenXe.objects.create(
                tuyenXeID=id_moi,
                tenTuyen=ten_tuyen,
                diemDi=diem_di,
                diemDen=diem_den,
                QuangDuong=quang_duong if quang_duong else None,
                DiemTrungGian=diem_trung_gian if diem_trung_gian else None,
                ThoiGian=thoi_gian if thoi_gian else None,
                nhaXe=nha_xe_obj
            )
            messages.success(request, 'Thêm tuyến xe thành công')
            return redirect('quanlytuyenxe')
        except Exception as e:
            messages.error(request, f'Lỗi hệ thống: {e}')
            return redirect('them_tuyen_xe')
            
    return render(request, 'nhaxe/form_tuyen_xe.html', {
        'tieu_de_form': 'Thêm tuyến mới',
        'tuyen': {},
        'nha_xe': Nhaxe.objects.filter(NhaxeID=nha_xe_id).first()
    })

def sua_tuyen_xe(request, ma_tuyen):
    '''
    Hiển thị form và xử lý chỉnh sửa tuyến xe
    '''
    nha_xe_id = request.session.get('user_id')
    if not nha_xe_id:
        messages.error(request, 'Vui lòng đăng nhập để sửa tuyến xe.')
        return redirect('dangnhap')

    du_lieu_tuyen = get_object_or_404(TuyenXe, pk=ma_tuyen)
    
    # Kiểm tra quyền
    if du_lieu_tuyen.nhaXe_id != nha_xe_id:
        messages.error(request, 'Bạn không có quyền sửa tuyến xe này.')
        return redirect('quanlytuyenxe')

    if request.method == 'POST':
        ten_tuyen = request.POST.get('tenTuyen')
        diem_di = request.POST.get('diemDi')
        diem_den = request.POST.get('diemDen')
        quang_duong = request.POST.get('quangDuong')
        diem_trung_gian = request.POST.get('diemTrungGian')
        thoi_gian = request.POST.get('thoiGian')

        # Nếu người dùng để trống quãng đường HOẶC thời gian, gọi OSRM để tính toán
        if not quang_duong or not quang_duong.strip() or not thoi_gian or not thoi_gian.strip():
            kq_quang_duong, kq_thoi_gian = tinh_quang_duong_osrm(diem_di, diem_den, diem_trung_gian)
            if not quang_duong or not quang_duong.strip():
                if kq_quang_duong is not None:
                    quang_duong = kq_quang_duong
            if not thoi_gian or not thoi_gian.strip():
                if kq_thoi_gian is not None:
                    thoi_gian = kq_thoi_gian

        try:
            du_lieu_tuyen.tenTuyen = ten_tuyen
            du_lieu_tuyen.diemDi = diem_di
            du_lieu_tuyen.diemDen = diem_den
            du_lieu_tuyen.QuangDuong = quang_duong if quang_duong else None
            du_lieu_tuyen.DiemTrungGian = diem_trung_gian if diem_trung_gian else None
            du_lieu_tuyen.ThoiGian = thoi_gian if thoi_gian else None
            du_lieu_tuyen.save()
            
            messages.success(request, 'Cập nhật tuyến xe thành công')
            return redirect('quanlytuyenxe')
        except Exception as e:
            messages.error(request, f'Lỗi hệ thống: {e}')
            
    return render(request, 'nhaxe/form_tuyen_xe.html', {
        'tieu_de_form': 'Chỉnh sửa tuyến',
        'tuyen': du_lieu_tuyen,
        'nha_xe': Nhaxe.objects.filter(NhaxeID=nha_xe_id).first()
    })

def xoa_tuyen_xe(request, ma_tuyen):
    '''
    Xử lý xóa tuyến xe ra khỏi hệ thống với thông báo thuần Việt
    '''
    ma_nha_xe = request.session.get('user_id')
    if not ma_nha_xe:
        return redirect('dangnhap')

    if request.method in ['POST', 'GET']:
        tuyen_xe_can_xoa = get_object_or_404(TuyenXe, pk=ma_tuyen)
        
        # Xác thực quyền sở hữu
        if tuyen_xe_can_xoa.nhaXe_id != ma_nha_xe:
            messages.error(request, 'Bạn không có quyền thực hiện thao tác này')
            return redirect('quanlytuyenxe')

        # Kiểm tra xem có chuyến xe nào đang hoạt động không (Chưa hoàn thành hoặc Đang chạy)
        co_chuyen_dang_chay = ChuyenXe.objects.filter(
            TuyenXe_id=ma_tuyen,
            TrangThai__in=['Chưa hoàn thành', 'Đang chạy']
        ).exists()

        if co_chuyen_dang_chay:
            messages.error(request, 'Không thể xóa tuyến đang có chuyến hoạt động')
            return redirect('quanlytuyenxe')

        # Thực hiện xóa
        try:
            ten_tuyen_da_xoa = tuyen_xe_can_xoa.tenTuyen
            tuyen_xe_can_xoa.delete()
            messages.success(request, f"Đã xóa tuyến xe {ten_tuyen_da_xoa}")
        except Exception as loi_he_thong:
            messages.error(request, f'Lỗi hệ thống: {loi_he_thong}')
            
    return redirect('quanlytuyenxe')