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
    """Tính quãng đường bằng OSRM (Open Source Routing Machine) - Miễn phí."""
    try:
        toa_do_di = lay_toa_do(diem_di)
        toa_do_den = lay_toa_do(diem_den)
        
        if not toa_do_di or not toa_do_den:
            return None

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
                return round(quang_duong_met / 1000.0, 1) 
    except Exception as e:
        print(f"Lỗi OSRM: {e}")
    return None

def quanlytuyenxe(request):
    nha_xe_id = request.session.get('user_id')
    if not nha_xe_id:
        return redirect('index')

    try:
        # Lấy danh sách tuyến xe trực tiếp từ Database
        danh_sach_tuyen = TuyenXe.objects.filter(nhaXe_id=nha_xe_id)
        
        # Danh sách tên tuyến để gợi ý
        tat_ca_ten_tuyen = list(TuyenXe.objects.values_list('tenTuyen', flat=True))
        
        # Tính toán ID mới
        all_ids = TuyenXe.objects.values_list('tuyenXeID', flat=True)
        max_id = 0
        for tx_id in all_ids:
            if tx_id and tx_id.startswith('TX') and tx_id[2:].isdigit():
                num = int(tx_id[2:])
                if num > max_id:
                    max_id = num
        
        ma_tuyen_xe_moi = f"TX{max_id + 1:04d}"

        context = {
            'nha_xe_id': nha_xe_id,
            'danh_sach_tuyen': danh_sach_tuyen,
            'ma_tuyen_xe_moi': ma_tuyen_xe_moi,
            'tat_ca_ten_tuyen_json': json.dumps(tat_ca_ten_tuyen)
        }
        return render(request, 'home/quanlytuyenxe.html', context)
    except Exception as e:
        messages.error(request, f'Lỗi lấy dữ liệu tuyến xe: {str(e)}')
        return render(request, 'home/quanlytuyenxe.html', {'danh_sach_tuyen': []})

def them_tuyen_xe(request):
    if request.method == 'POST':
        nha_xe_id = request.session.get('user_id')
        if not nha_xe_id:
            return redirect('index')

        ten_tuyen = request.POST.get('tenTuyen')
        diem_di = request.POST.get('diemDi')
        diem_den = request.POST.get('diemDen')
        quang_duong = request.POST.get('quangDuong')
        diem_trung_gian = request.POST.get('diemTrungGian')
        
        # Tự động tính quãng đường nếu để trống
        if not quang_duong or not quang_duong.strip():
            kq_tinh_toan = tinh_quang_duong_osrm(diem_di, diem_den, diem_trung_gian)
            if kq_tinh_toan is not None:
                quang_duong = kq_tinh_toan

        try:
            # 1. Tính ID mới
            all_ids = TuyenXe.objects.values_list('tuyenXeID', flat=True)
            max_id = 0
            for tx_id in all_ids:
                if tx_id and tx_id.startswith('TX') and tx_id[2:].isdigit():
                    num = int(tx_id[2:])
                    if num > max_id:
                        max_id = num
            next_id = f"TX{max_id + 1:04d}"

            # 2. Lưu vào Database
            nha_xe_obj = Nhaxe.objects.get(NhaxeID=nha_xe_id)
            TuyenXe.objects.create(
                tuyenXeID=next_id,
                nhaXe=nha_xe_obj,
                tenTuyen=ten_tuyen,
                diemDi=diem_di,
                diemDen=diem_den,
                QuangDuong=quang_duong if quang_duong else None,
                DiemTrungGian=diem_trung_gian if diem_trung_gian else None
            )
            messages.success(request, 'Thêm tuyến xe thành công')
            return redirect('quanlytuyenxe')
        except Nhaxe.DoesNotExist:
            messages.error(request, f'Lỗi: Nhà xe {nha_xe_id} không tồn tại.')
        except Exception as e:
            messages.error(request, f'Lỗi hệ thống: {str(e)}')
            
    return render(request, 'home/form_tuyen_xe.html', {
        'tieu_de_form': 'Thêm tuyến mới',
        'tuyen': {}
    })

def sua_tuyen_xe(request, pk):
    du_lieu_tuyen = get_object_or_404(TuyenXe, pk=pk)

    if request.method == 'POST':
        ten_tuyen = request.POST.get('tenTuyen')
        diem_di = request.POST.get('diemDi')
        diem_den = request.POST.get('diemDen')
        quang_duong = request.POST.get('quangDuong')
        diem_trung_gian = request.POST.get('diemTrungGian')
        
        if not quang_duong or not quang_duong.strip():
            kq_tinh_toan = tinh_quang_duong_osrm(diem_di, diem_den, diem_trung_gian)
            if kq_tinh_toan is not None:
                quang_duong = kq_tinh_toan

        try:
            du_lieu_tuyen.tenTuyen = ten_tuyen
            du_lieu_tuyen.diemDi = diem_di
            du_lieu_tuyen.diemDen = diem_den
            du_lieu_tuyen.QuangDuong = quang_duong if quang_duong else None
            du_lieu_tuyen.DiemTrungGian = diem_trung_gian if diem_trung_gian else None
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
        try:
            # Kiểm tra xem có chuyến xe nào đang sử dụng tuyến này không
            if ChuyenXe.objects.filter(TuyenXe_id=pk).exists():
                messages.error(request, 'Không thể xóa tuyến xe, có chuyến đang hoạt động')
                return redirect('quanlytuyenxe')

            TuyenXe.objects.filter(tuyenXeID=pk).delete()
            messages.success(request, 'Xóa tuyến xe thành công')
        except Exception as e:
            messages.error(request, f'Lỗi khi xóa: {str(e)}')
            
    return redirect('quanlytuyenxe')
