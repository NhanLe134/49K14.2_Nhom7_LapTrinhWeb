from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import TuyenXe, Nhaxe, ChuyenXe # Import models trực tiếp
import json

# Giữ nguyên các hàm tính toán bổ trợ
def lay_toa_do(ten_dia_diem):
    import requests
    if not ten_dia_diem: return None
    try:
        duong_dan = "https://nominatim.openstreetmap.org/search"
        tham_so = {"q": f"{ten_dia_diem}, Việt Nam", "format": "json", "limit": 1}
        phan_hoi = requests.get(duong_dan, params=tham_so, headers={'User-Agent': 'VexeApp/1.0'})
        if phan_hoi.status_code == 200:
            du_lieu = phan_hoi.json()
            if du_lieu: return {"lat": du_lieu[0]["lat"], "lon": du_lieu[0]["lon"]}
    except: pass
    return None

def tinh_quang_duong_osrm(diem_di, diem_den, ds_trung_gian_str=None):
    import requests
    try:
        toa_do_di = lay_toa_do(diem_di)
        toa_do_den = lay_toa_do(diem_den)
        if not toa_do_di or not toa_do_den: return None
        danh_sach_toa_do = [f"{toa_do_di['lon']},{toa_do_di['lat']}"]
        if ds_trung_gian_str:
            for p in [x.strip() for x in ds_trung_gian_str.split(",") if x.strip()]:
                toa_tg = lay_toa_do(p)
                if toa_tg: danh_sach_toa_do.append(f"{toa_tg['lon']},{toa_tg['lat']}")
        danh_sach_toa_do.append(f"{toa_do_den['lon']},{toa_do_den['lat']}")
        duong_dan = f"https://router.project-osrm.org/route/v1/driving/{';'.join(danh_sach_toa_do)}?overview=false"
        phan_hoi = requests.get(duong_dan)
        if phan_hoi.status_code == 200:
            du_lieu = phan_hoi.json()
            if du_lieu.get("code") == "Ok": return round(du_lieu["routes"][0]["distance"] / 1000.0, 1)
    except: pass
    return None

# --- CÁC HÀM VIEW SỬ DỤNG DATABASE (ORM) ---

def quanlytuyenxe(request):
    nha_xe_id = request.session.get('user_id')
    
    # Lấy danh sách tuyến xe của nhà xe này từ Database
    print(f"DEBUG: Dang truy cap voi nha_xe_id trong session = {nha_xe_id}")
    danh_sach_tuyen = TuyenXe.objects.filter(nhaXe_id=nha_xe_id)
    
    # Lấy tất cả tên tuyến xe để gửi xuống JS (xử lý trùng tên)
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
        
        # Tự động tính quãng đường
        if not quang_duong or not quang_duong.strip():
            kq = tinh_quang_duong_osrm(diem_di, diem_den, diem_trung_gian)
            if kq: quang_duong = str(kq)

        # Tạo ID tự động (TX0001, TX0002...)
        last_tuyen = TuyenXe.objects.all().order_by('tuyenXeID').last()
        num = 1
        if last_tuyen and last_tuyen.tuyenXeID.startswith('TX'):
            num = int(last_tuyen.tuyenXeID[2:]) + 1
        id_moi = f"TX{num:04d}"

        try:
            nha_xe_obj = Nhaxe.objects.get(NhaxeID=nha_xe_id)
            TuyenXe.objects.create(
                tuyenXeID=id_moi,
                nhaXe=nha_xe_obj,
                tenTuyen=ten_tuyen,
                diemDi=diem_di,
                diemDen=diem_den,
                QuangDuong=quang_duong,
                DiemTrungGian=diem_trung_gian
            )
            messages.success(request, 'Thêm tuyến xe thành công')
            return redirect('quanlytuyenxe')
        except Exception as e:
            messages.error(request, f'Lỗi khi lưu vào Database: {e}')
            
    return render(request, 'home/form_tuyen_xe.html', {
        'tieu_de_form': 'Thêm tuyến mới',
        'tuyen': {}
    })

def sua_tuyen_xe(request, pk):
    # Lấy đối tượng từ DB
    tuyen_obj = get_object_or_404(TuyenXe, pk=pk)

    if request.method == 'POST':
        tuyen_obj.tenTuyen = request.POST.get('tenTuyen')
        tuyen_obj.diemDi = request.POST.get('diemDi')
        tuyen_obj.diemDen = request.POST.get('diemDen')
        quang_duong = request.POST.get('quangDuong')
        tuyen_obj.DiemTrungGian = request.POST.get('diemTrungGian')
        
        if not quang_duong or not quang_duong.strip():
            kq = tinh_quang_duong_osrm(tuyen_obj.diemDi, tuyen_obj.diemDen, tuyen_obj.DiemTrungGian)
            if kq: quang_duong = str(kq)
        
        tuyen_obj.QuangDuong = quang_duong
        tuyen_obj.save()
        
        messages.success(request, 'Cập nhật tuyến xe thành công')
        return redirect('quanlytuyenxe')
            
    return render(request, 'home/form_tuyen_xe.html', {
        'tieu_de_form': 'Chỉnh sửa tuyến',
        'tuyen': tuyen_obj
    })

def xoa_tuyen_xe(request, pk):
    if request.method == 'POST':
        # Kiểm tra xem có chuyến xe nào đang dùng tuyến này không
        if ChuyenXe.objects.filter(TuyenXe_id=pk).exists():
            messages.error(request, 'Không thể xóa tuyến xe, có chuyến đang hoạt động')
        else:
            TuyenXe.objects.filter(pk=pk).delete()
            messages.success(request, 'Xóa tuyến xe thành công')
            
    return redirect('quanlytuyenxe')