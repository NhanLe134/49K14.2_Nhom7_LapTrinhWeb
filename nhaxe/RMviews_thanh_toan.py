from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Ve, ThanhToan, Nhaxe, User_Authentication, KhachHang, NganHangAdmin
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.conf import settings
import json
import re
from decimal import Decimal

def lay_ngan_hang_quan_tri():
    cau_hinh = NganHangAdmin.objects.first()
    if cau_hinh:
        return {
            'ma_ngan_hang': cau_hinh.MaNganHang,
            'so_tai_khoan': cau_hinh.SoTaiKhoan,
            'ten_chu_tai_khoan': cau_hinh.TenChuTaiKhoan
        }
    # Dự phòng nếu cơ sở dữ liệu trống
    return {
        'ma_ngan_hang': 'MB',
        'so_tai_khoan': '0352149424',
        'ten_chu_tai_khoan': 'DANG NGOC ANH THU'
    }

DANH_SACH_NGAN_HANG = [
    {'id': 'MB', 'name': 'MB Bank (Ngân hàng Quân Đội)'},
    {'id': 'VCB', 'name': 'Vietcombank'},
    {'id': 'BIDV', 'name': 'BIDV'},
    {'id': 'ICB', 'name': 'VietinBank'},
    {'id': 'VBA', 'name': 'Agribank'},
    {'id': 'TCB', 'name': 'Techcombank'},
    {'id': 'ACB', 'name': 'ACB'},
    {'id': 'VPB', 'name': 'VPBank'},
    {'id': 'TPB', 'name': 'TPBank'},
    {'id': 'STB', 'name': 'Sacombank'},
    {'id': 'HDB', 'name': 'HDBank'},
    {'id': 'VIB', 'name': 'VIB'},
    {'id': 'SHB', 'name': 'SHB'},
    {'id': 'MSB', 'name': 'MSB'},
    {'id': 'VCCB', 'name': 'VietCapitalBank'},
    {'id': 'SCB', 'name': 'SCB'},
    {'id': 'LPB', 'name': 'LienVietPostBank'},
]

def tao_ma_thanh_toan_tu_dong():
    thanh_toan_cu_nhat = ThanhToan.objects.all().order_by('ThanhToanID').last()
    if not thanh_toan_cu_nhat: return "TT0001"
    ket_qua_khop = re.search(r'\d+', thanh_toan_cu_nhat.ThanhToanID)
    ma_tiep_theo = int(ket_qua_khop.group()) + 1 if ket_qua_khop else 1
    return f"TT{ma_tiep_theo:04d}"

def gui_mail_ve(ve_doi_tuong, loai='thanh_toan'):
    """Gửi email thông báo cho khách hàng (đặt vé hoặc thanh toán)."""
    try:
        # Lấy địa chỉ email nhận
        email_nhan = ve_doi_tuong.KhachHang.Email
        if not email_nhan:
            nguoi_dung = User_Authentication.objects.filter(KhachHang=ve_doi_tuong.KhachHang).first()
            email_nhan = nguoi_dung.email if nguoi_dung else None
        
        if not email_nhan: return False

        # Chọn mẫu giao diện và tiêu đề
        if loai == 'dat_ve':
            ten_mau = 'emails/booking_success.html'
            tieu_de = f"[VexeApp] Thông báo đặt vé thành công - #{ve_doi_tuong.VeID}"
        else:
            ten_mau = 'emails/payment_success.html'
            tieu_de = f"[VexeApp] Xác nhận thanh toán thành công - Mã vé: {ve_doi_tuong.VeID}"

        # Định dạng dữ liệu hiển thị
        gia_ve_chuoi = "{:,.0f}".format(ve_doi_tuong.GiaVe).replace(',', '.')
        ma_ghe = ve_doi_tuong.Ghe.soGhe if ve_doi_tuong.Ghe else "N/A"
        
        noi_dung_html = render_to_string(ten_mau, {
            've': ve_doi_tuong,
            'ma_ghe': ma_ghe,
            'gia_ve_format': gia_ve_chuoi
        })
        
        thu_dien_tu = EmailMessage(tieu_de, noi_dung_html, settings.DEFAULT_FROM_EMAIL, [email_nhan])
        thu_dien_tu.content_subtype = "html"
        thu_dien_tu.send(fail_silently=True)
        return True
    except Exception as loi:
        print(f"Lỗi gửi mail {loai}: {loi}")
        return False

def xu_ly_thanh_toan(request, ve_id):
    ve_doi_tuong = get_object_or_404(Ve, pk=ve_id)
    nha_xe_doi_tuong = ve_doi_tuong.ChuyenXe.TuyenXe.nhaXe
    thanh_toan_hop_le = all([nha_xe_doi_tuong.MaNganHang, nha_xe_doi_tuong.SoTaiKhoan])
    
    # Lấy thông tin ngân hàng quản trị
    ngan_hang_quan_tri = lay_ngan_hang_quan_tri()
    
    duong_dan_qr = None
    if thanh_toan_hop_le:
        so_tien = 2000 # Số tiền thử nghiệm
        noi_dung = f"THANH TOAN VE {ve_doi_tuong.VeID}"
        duong_dan_qr = f"https://img.vietqr.io/image/{ngan_hang_quan_tri['ma_ngan_hang']}-{ngan_hang_quan_tri['so_tai_khoan']}-compact.png?amount={so_tien}&addInfo={noi_dung}&accountName={ngan_hang_quan_tri['ten_chu_tai_khoan']}"
    
    return render(request, 'khachhang/thanhtoan.html', {
        've': ve_doi_tuong, 
        'qr_url': duong_dan_qr, 
        'thanh_to_an_online_kha_dung': thanh_toan_hop_le, 
        'thong_tin_ngan_hang': ngan_hang_quan_tri
    })

def xac_nhan_thanh_toan_thu_cong(request, ve_id):
    if request.method == 'POST':
        ve_doi_tuong = get_object_or_404(Ve, pk=ve_id)
        phuong_thuc = request.POST.get('phuong_thuc')
        if phuong_thuc == 'Tiền mặt':
            ve_doi_tuong.TrangThaiThanhToan = "Chưa thanh toán"
            ve_doi_tuong.save()
        else:
            ThanhToan.objects.get_or_create(Ve=ve_doi_tuong, defaults={'ThanhToanID': tao_ma_thanh_toan_tu_dong(), 'SoTien': ve_doi_tuong.GiaVe, 'NgayThanhToan': timezone.now(), 'DaQuyetToan': False})
            ve_doi_tuong.TrangThaiThanhToan = "Chưa thanh toán"
            ve_doi_tuong.save()
            messages.success(request, "Vui lòng chuyển khoản để hoàn tất.")
        return redirect('quanlyve')
    return redirect('quanlyve')

@csrf_exempt
def nhan_thong_bao_thanh_toan_tu_dong(request):
    try:
        du_lieu = json.loads(request.body)
        noi_dung = du_lieu.get('content', '') or du_lieu.get('transaction_content', '')
        khop_ve = re.search(r'VE\d+', noi_dung.upper())
        if khop_ve:
            ve_doi_tuong = Ve.objects.filter(VeID=khop_ve.group(0)).first()
            if ve_doi_tuong:
                ve_doi_tuong.TrangThaiThanhToan = "Đã thanh toán"
                ve_doi_tuong.save()
                ThanhToan.objects.update_or_create(Ve=ve_doi_tuong, defaults={'ThanhToanID': tao_ma_thanh_toan_tu_dong() if not hasattr(ve_doi_tuong, 'thanhtoan') else ve_doi_tuong.thanhtoan.ThanhToanID, 'SoTien': du_lieu.get('transfer_amount', 0), 'NgayThanhToan': timezone.now(), 'DaQuyetToan': False})
                
                # Gửi mail xác nhận thanh toán thành công
                gui_mail_ve(ve_doi_tuong, loai='thanh_toan')
                
                return JsonResponse({'status': 'success'})
    except: pass
    return JsonResponse({'status': 'error'})

def kiem_tra_trang_thai_ve(request, ve_id):
    ve_doi_tuong = Ve.objects.filter(VeID=ve_id).first()
    return JsonResponse({'da_thanh_toan': (ve_doi_tuong.TrangThaiThanhToan == "Đã thanh toán") if ve_doi_tuong else False})

def khach_hang_lich_su_giao_dich(request):
    ma_nguoi_dung = request.session.get('user_id')
    xac_thuc = User_Authentication.objects.filter(UserID=ma_nguoi_dung).first()
    if not xac_thuc or xac_thuc.Vaitro != 'KhachHang': return redirect('dangnhap')
    danh_sach = ThanhToan.objects.filter(Ve__KhachHang=xac_thuc.KhachHang).order_by('-NgayThanhToan')
    return render(request, 'khachhang/lich_su_giao_dich.html', {'danh_sach_giao_dich': danh_sach})

def nha_xe_bao_cao_doanh_thu(request):
    ma_nguoi_dung = request.session.get('user_id')
    if not ma_nguoi_dung: return redirect('dangnhap')
    xac_thuc = User_Authentication.objects.filter(UserID=ma_nguoi_dung).first()
    if not xac_thuc or xac_thuc.Vaitro != 'Nhaxe': return redirect('index')
    nha_xe_doi_tuong = xac_thuc.Nhaxe
    if not nha_xe_doi_tuong: nha_xe_doi_tuong = Nhaxe.objects.filter(Email=xac_thuc.username).first()
    if not nha_xe_doi_tuong: return redirect('index')
    
    giao_dich_cho_duyet = ThanhToan.objects.filter(Ve__ChuyenXe__TuyenXe__nhaXe=nha_xe_doi_tuong, Ve__TrangThaiThanhToan="Đã thanh toán", DaQuyetToan=False).select_related('Ve').order_by('-NgayThanhToan')
    giao_dich_da_xong = ThanhToan.objects.filter(Ve__ChuyenXe__TuyenXe__nhaXe=nha_xe_doi_tuong, Ve__TrangThaiThanhToan="Đã thanh toán", DaQuyetToan=True).select_related('Ve').order_by('-NgayThanhToan')
    
    tong_doanh_thu = sum(p.SoTien for p in giao_dich_cho_duyet)
    ti_le_phi = Decimal(str(getattr(nha_xe_doi_tuong, 'PhanTramHoaHong', 10.0) or 10.0)) / Decimal('100')
    tong_hoa_hong = Decimal(str(tong_doanh_thu)) * ti_le_phi
    thuc_nhan = Decimal(str(tong_doanh_thu)) - tong_hoa_hong
    
    return render(request, 'nhaxe/bao_cao_doanh_thu.html', {
        'nha_xe': nha_xe_doi_tuong, 
        'danh_sach_cho_duyet': giao_dich_cho_duyet, 
        'danh_sach_da_xong': giao_dich_da_xong, 
        'tong_doanh_thu': tong_doanh_thu, 
        'tong_hoa_hong': tong_hoa_hong, 
        'thuc_nhan': thuc_nhan
    })

def nha_xe_cau_hinh_ngan_hang(request):
    ma_nguoi_dung = request.session.get('user_id')
    xac_thuc = User_Authentication.objects.filter(UserID=ma_nguoi_dung).first()
    if not xac_thuc or xac_thuc.Vaitro != 'Nhaxe': return redirect('index')
    nha_xe_doi_tuong = xac_thuc.Nhaxe
    if not nha_xe_doi_tuong: nha_xe_doi_tuong = Nhaxe.objects.filter(Email=xac_thuc.username).first()
    if not nha_xe_doi_tuong: return redirect('index')
    
    if request.method == 'POST':
        nha_xe_doi_tuong.MaNganHang = request.POST.get('ma_ngan_hang')
        nha_xe_doi_tuong.SoTaiKhoan = request.POST.get('so_tai_khoan')
        nha_xe_doi_tuong.TenChuTaiKhoan = request.POST.get('ten_chu_tai_khoan', '').upper()
        nha_xe_doi_tuong.save()
        messages.success(request, "Cập nhật thành công!")
        
    return render(request, 'nhaxe/cau_hinh_ngan_hang.html', {
        'nhaxe': nha_xe_doi_tuong,
        'nha_xe': nha_xe_doi_tuong,
        'danh_sach_ngan_hang': DANH_SACH_NGAN_HANG
    })

# ==================== PHẦN DÀNH CHO QUẢN TRỊ VIÊN ====================

def quan_tri_kiem_tra_quyen(request):
    ma_nguoi_dung = request.session.get('user_id')
    xac_thuc = User_Authentication.objects.filter(UserID=ma_nguoi_dung).first()
    if not xac_thuc or xac_thuc.Vaitro != 'Admin':
        return None
    return xac_thuc

def quan_tri_bang_dieu_khien_quyet_toan(request):
    nguoi_quan_tri = quan_tri_kiem_tra_quyen(request)
    if not nguoi_quan_tri: return redirect('dangnhap')
    
    bao_cao_nha_xe = []
    danh_sach_nha_xe = Nhaxe.objects.all()
    
    for nx in danh_sach_nha_xe:
        giao_dich_cho = ThanhToan.objects.filter(
            Ve__ChuyenXe__TuyenXe__nhaXe=nx, 
            DaQuyetToan=False, 
            Ve__TrangThaiThanhToan="Đã thanh toán"
        )
        
        if giao_dich_cho.exists():
            tong_tien = sum(t.SoTien for t in giao_dich_cho)
            ti_le_phi = Decimal(str(getattr(nx, 'PhanTramHoaHong', 10.0) or 10.0)) / Decimal('100')
            thuc_nhan = Decimal(str(tong_tien)) * (1 - ti_le_phi)
            
            bao_cao_nha_xe.append({
                'nhaxe': nx,
                'so_giao_dich': giao_dich_cho.count(),
                'thuc_nhan': thuc_nhan
            })
    
    return render(request, 'admin/quan_ly_quyet_toan.html', {'bao_cao_nhaxe': bao_cao_nha_xe})

def quan_tri_xac_nhan_quyet_toan(request, nhaxe_id):
    nguoi_quan_tri = quan_tri_kiem_tra_quyen(request)
    if not nguoi_quan_tri: return redirect('dangnhap')
    
    nha_xe_doi_tuong = get_object_or_404(Nhaxe, pk=nhaxe_id)
    
    # 1. Lọc giao dịch chưa quyết toán
    giao_dich_cho = ThanhToan.objects.filter(
        Ve__ChuyenXe__TuyenXe__nhaXe=nha_xe_doi_tuong, 
        DaQuyetToan=False, 
        Ve__TrangThaiThanhToan="Đã thanh toán"
    )
    
    if not giao_dich_cho.exists():
        messages.warning(request, "Không có giao dịch nào cần quyết toán.")
        return redirect('admin_dashboard_quyet_toan')
        
    # 2. Tính toán số tiền để gửi mail
    tong_tien = sum(t.SoTien for t in giao_dich_cho)
    ti_le_phi = Decimal(str(getattr(nha_xe_doi_tuong, 'PhanTramHoaHong', 10.0) or 10.0)) / Decimal('100')
    thuc_nhan = Decimal(str(tong_tien)) * (1 - ti_le_phi)
    so_luong_ve = giao_dich_cho.count()

    # 3. Cập nhật trạng thái trong DB
    giao_dich_cho.update(DaQuyetToan=True)
    
    # 4. Gửi mail thông báo HTML cho nhà xe
    try:
        tieu_de = f"[VexeApp] Thông báo quyết toán thành công - {nha_xe_doi_tuong.TenNhaXe}"
        
        # Định dạng tiền tệ
        tong_tien_chuoi = "{:,.0f}".format(tong_tien).replace(',', '.')
        hoa_hong_chuoi = "{:,.0f}".format(tong_tien * ti_le_phi).replace(',', '.')
        thuc_nhan_chuoi = "{:,.0f}".format(thuc_nhan).replace(',', '.')
        
        noi_dung_html = render_to_string('emails/settlement_notification.html', {
            'nx': nha_xe_doi_tuong,
            'so_luong': so_luong_ve,
            'tong_tien_format': tong_tien_chuoi,
            'hoa_hong_format': hoa_hong_chuoi,
            'thuc_nhan_format': thuc_nhan_chuoi
        })
        
        thu_dien_tu = EmailMessage(tieu_de, noi_dung_html, settings.DEFAULT_FROM_EMAIL, [nha_xe_doi_tuong.Email])
        thu_dien_tu.content_subtype = "html"
        thu_dien_tu.send(fail_silently=True)
    except Exception as loi:
        print(f"Lỗi gửi mail quyết toán: {loi}")

    messages.success(request, f"Đã quyết toán và gửi mail thông báo cho nhà xe {nha_xe_doi_tuong.TenNhaXe}")
    return redirect('admin_dashboard_quyet_toan')

def quan_tri_danh_sach_nha_xe(request):
    nguoi_quan_tri = quan_tri_kiem_tra_quyen(request)
    if not nguoi_quan_tri: return redirect('dangnhap')
    
    danh_sach = Nhaxe.objects.all().order_by('NhaxeID')
    return render(request, 'admin/list_nhaxe.html', {'danh_sach_nhaxe': danh_sach})

def quan_tri_danh_sach_khach_hang(request):
    nguoi_quan_tri = quan_tri_kiem_tra_quyen(request)
    if not nguoi_quan_tri: return redirect('dangnhap')
    
    danh_sach = KhachHang.objects.all().order_by('KhachHangID')
    for kh in danh_sach:
        xac_thuc = User_Authentication.objects.filter(KhachHang=kh).first()
        kh.SDT = xac_thuc.SoDienThoai if xac_thuc else "Chưa có"
        
    return render(request, 'admin/list_khachhang.html', {'danh_sach_khachhang': danh_sach})

def quan_tri_cau_hinh_ngan_hang(request):
    nguoi_quan_tri = quan_tri_kiem_tra_quyen(request)
    if not nguoi_quan_tri: return redirect('dangnhap')
    
    cau_hinh_ngan_hang = NganHangAdmin.objects.first()
    
    if request.method == 'POST':
        ten_chu_tai_khoan = request.POST.get('ten_chu_tai_khoan', '').upper()
        ma_ngan_hang = request.POST.get('ma_ngan_hang')
        so_tai_khoan = request.POST.get('so_tai_khoan')
        
        if cau_hinh_ngan_hang:
            cau_hinh_ngan_hang.TenChuTaiKhoan = ten_chu_tai_khoan
            cau_hinh_ngan_hang.MaNganHang = ma_ngan_hang
            cau_hinh_ngan_hang.SoTaiKhoan = so_tai_khoan
            cau_hinh_ngan_hang.save()
        else:
            NganHangAdmin.objects.create(
                TenChuTaiKhoan=ten_chu_tai_khoan,
                MaNganHang=ma_ngan_hang,
                SoTaiKhoan=so_tai_khoan
            )
        messages.success(request, "Cấu hình ngân hàng Admin đã được cập nhật!")
        return redirect('admin_cau_hinh_ngan_hang')

    return render(request, 'admin/cau_hinh_ngan_hang.html', {
        'cau_hinh': cau_hinh_ngan_hang,
        'danh_sach_ngan_hang': DANH_SACH_NGAN_HANG
    })
