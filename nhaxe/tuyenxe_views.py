from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import TuyenXe, Nhaxe, ChuyenXe
import requests
import json

def anh_xa_dia_diem(ten_dia_diem):
    """Bản đồ ánh xạ các tên điểm đặc biệt sang tọa độ Plus Code cụ thể."""
    ten_thap_len = ten_dia_diem.strip().lower()
    if ten_thap_len == "huế":
        return "FH7V+7Q Thuận Hóa, Huế, Việt Nam"
    elif ten_thap_len == "đà nẵng":
        return "36CJ+H3 An Hải, Đà Nẵng, Việt Nam"
    elif ten_thap_len == "hội an":
        return "V8GG+7MR, An Hội, Hội An, Đà Nẵng, Việt Nam"
    return ten_dia_diem

def lay_toa_do(ten_dia_diem):
    """Lấy tọa độ từ Nominatim (OpenStreetMap) - Miễn phí."""
    if not ten_dia_diem:
        return None
    try:
        duong_dan = "https://nominatim.openstreetmap.org/search"
        tham_so = {
            "q": f"{ten_dia_diem}, Việt Nam",
            "format": "json",
            "limit": 1
        }
        tieu_de = {'User-Agent': 'VexeApp/1.0'}
        phan_hoi = requests.get(duong_dan, params=tham_so, headers=tieu_de)
        if phan_hoi.status_code == 200:
            du_lieu = phan_hoi.json()
            if du_lieu:
                return {"lat": du_lieu[0]["lat"], "lon": du_lieu[0]["lon"]}
    except Exception as e:
        print(f"Lỗi lấy tọa độ: {e}")
    return None

def tinh_quang_duong_osrm(diem_di, diem_den, ds_trung_gian_str=None):
    """Tính quãng đường và thời gian bằng OSRM (Open Source Routing Machine) - Miễn phí."""
    try:
        toa_do_di = lay_toa_do(diem_di)
        toa_do_den = lay_toa_do(diem_den)
        
        if not toa_do_di or not toa_do_den:
            return None, None

        danh_sach_toa_do = [f"{toa_do_di['lon']},{toa_do_di['lat']}"]
        
        if ds_trung_gian_str:
            cac_diem_tg = [p.strip() for p in ds_trung_gian_str.split(",") if p.strip()]
            for p in cac_diem_tg:
                toa_do_tg = lay_toa_do(p)
                if toa_do_tg:
                    danh_sach_toa_do.append(f"{toa_do_tg['lon']},{toa_do_tg['lat']}")
        
        danh_sach_toa_do.append(f"{toa_do_den['lon']},{toa_do_den['lat']}")
        duong_di_toa_do = ";".join(danh_sach_toa_do)

        duong_dan = f"https://router.project-osrm.org/route/v1/driving/{duong_di_toa_do}?overview=false"
        phan_hoi = requests.get(duong_dan)
        if phan_hoi.status_code == 200:
            du_lieu = phan_hoi.json()
            if du_lieu.get("code") == "Ok" and du_lieu.get("routes"):
                quang_duong_met = du_lieu["routes"][0]["distance"]
                thoi_gian_giay = du_lieu["routes"][0]["duration"]
                # Nhân đôi thời gian dự kiến (vì phải đón trả khách)
                thoi_gian_gio = (thoi_gian_giay / 3600.0) * 2
                return round(quang_duong_met / 1000.0, 1), round(thoi_gian_gio, 1)
    except Exception as e:
        print(f"Lỗi OSRM: {e}")
    return None, None

def quanlytuyenxe(request):
    nha_xe_id = request.session.get('user_id')

    # Lấy từ Database thay vì API
    danh_sach_tuyen = TuyenXe.objects.filter(nhaXe_id=nha_xe_id)
    tat_ca_ten_tuyen = list(TuyenXe.objects.values_list('tenTuyen', flat=True))
    
    context = {
        'nha_xe_id': nha_xe_id,
        'danh_sach_tuyen': danh_sach_tuyen,
        'tat_ca_ten_tuyen_json': json.dumps(tat_ca_ten_tuyen)
    }
    return render(request, 'home/quanlytuyenxe.html', context)

def them_tuyen_xe(request):
    if request.method == 'POST':
        nha_xe_id = request.session.get('user_id')

        ten_tuyen = request.POST.get('tenTuyen')
        diem_di = request.POST.get('diemDi')
        diem_den = request.POST.get('diemDen')
        quang_duong = request.POST.get('quangDuong')
        diem_trung_gian = request.POST.get('diemTrungGian')
        thoi_gian = request.POST.get('thoiGian')

        # Nếu người dùng để trống quãng đường HOẶC thời gian, gọi API để tính toán
        if not quang_duong or not quang_duong.strip() or not thoi_gian or not thoi_gian.strip():
            kq_quang_duong, kq_thoi_gian = tinh_quang_duong_osrm(diem_di, diem_den, diem_trung_gian)
            if not quang_duong or not quang_duong.strip():
                if kq_quang_duong is not None:
                    quang_duong = int(kq_quang_duong)
            if not thoi_gian or not thoi_gian.strip():
                if kq_thoi_gian is not None:
                    thoi_gian = kq_thoi_gian

        # Tìm ID lớn nhất trong DB
        last_route = TuyenXe.objects.all().order_by('tuyenXeID').last()
        max_id = 0
        if last_route and last_route.tuyenXeID.startswith('TX'):
             max_id = int(last_route.tuyenXeID[2:])

        id_moi = f"TX{max_id + 1:04d}"

        # Lưu trực tiếp vào Database thông qua model TuyenXe
        try:
            nha_xe_obj = Nhaxe.objects.get(NhaxeID=nha_xe_id)
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
        except Nhaxe.DoesNotExist:
            messages.error(request, f'Lỗi: Nhà xe {nha_xe_id} không tồn tại trong DB.')
        except Exception as e:
            messages.error(request, f'Lỗi hệ thống: {e}')
            
    return render(request, 'home/form_tuyen_xe.html', {
        'tieu_de_form': 'Thêm tuyến mới',
        'tuyen': {}
    })

def sua_tuyen_xe(request, pk):
    # Lấy dữ liệu từ Database
    du_lieu_tuyen = get_object_or_404(TuyenXe, pk=pk)

    if request.method == 'POST':
        nha_xe_id = request.session.get('user_id')

        ten_tuyen = request.POST.get('tenTuyen')
        diem_di = request.POST.get('diemDi')
        diem_den = request.POST.get('diemDen')
        quang_duong = request.POST.get('quangDuong')
        diem_trung_gian = request.POST.get('diemTrungGian')
        thoi_gian = request.POST.get('thoiGian')

        # Nếu người dùng để trống quãng đường HOẶC thời gian, gọi API để tính toán
        if not quang_duong or not quang_duong.strip() or not thoi_gian or not thoi_gian.strip():
            kq_quang_duong, kq_thoi_gian = tinh_quang_duong_osrm(diem_di, diem_den, diem_trung_gian)
            if not quang_duong or not quang_duong.strip():
                if kq_quang_duong is not None:
                    quang_duong = int(kq_quang_duong)
            if not thoi_gian or not thoi_gian.strip():
                if kq_thoi_gian is not None:
                    thoi_gian = kq_thoi_gian

        # Cập nhật object và lưu lại
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
            
    return render(request, 'home/form_tuyen_xe.html', {
        'tieu_de_form': 'Chỉnh sửa tuyến',
        'tuyen': du_lieu_tuyen
    })

def xoa_tuyen_xe(request, pk):
    if request.method == 'POST':
        nha_xe_id = request.session.get('user_id')

        # Xác thực chủ sở hữu tuyến xe (chống việc sửa DOM để xóa trộm tuyến của nhà xe khác)
        tuyen_xe = get_object_or_404(TuyenXe, pk=pk)
        if tuyen_xe.nhaXe_id != nha_xe_id:
            messages.error(request, 'Bạn không có quyền xóa tuyến xe này')
            return redirect('quanlytuyenxe')

        # Kiểm tra xem tuyến xe này có chuyến xe nào đang liên kết không
        chuyen_xe_dang_hoat_dong = ChuyenXe.objects.filter(TuyenXe_id=pk).exists()

        if chuyen_xe_dang_hoat_dong:
            messages.error(request, 'Không thể xóa tuyến xe này vì đang có chuyến xe chạy trên tuyến.')
            return redirect('quanlytuyenxe')

        # Xóa trong Database
        try:
            tuyen_xe.delete()
            messages.success(request, 'Xóa tuyến xe thành công')
        except Exception as e:
            messages.error(request, f'Lỗi hệ thống khi xóa: {e}')
            
    return redirect('quanlytuyenxe')