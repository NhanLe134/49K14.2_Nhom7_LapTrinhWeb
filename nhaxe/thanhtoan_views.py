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

def lay_ngan_hang_admin():
    cau_hinh = NganHangAdmin.objects.first()
    if cau_hinh:
        return {
            'ma_ngan_hang': cau_hinh.MaNganHang,
            'so_tai_khoan': cau_hinh.SoTaiKhoan,
            'ten_chu_tai_khoan': cau_hinh.TenChuTaiKhoan
        }
    # Fallback mặc định nếu DB trống
    return {
        'ma_ngan_hang': 'MB',
        'so_tai_khoan': '0352149424',
        'ten_chu_tai_khoan': 'DANG NGOC ANH THU'
    }

NGAN_HANG_ADMIN = lay_ngan_hang_admin()

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
    last_tt = ThanhToan.objects.all().order_by('ThanhToanID').last()
    if not last_tt: return "TT0001"
    match = re.search(r'\d+', last_tt.ThanhToanID)
    next_id = int(match.group()) + 1 if match else 1
    return f"TT{next_id:04d}"

def gui_mail_ve(ve, loai='payment', danh_sach_ve=None):
    """Gửi email thông báo cho khách hàng (đặt vé hoặc thanh toán)."""
    try:
        # Nếu không truyền danh sách, coi như chỉ có 1 vé
        if not danh_sach_ve:
            danh_sach_ve = [ve]
            
        # Lấy email đích (từ vé đầu tiên)
        target_email = ve.KhachHang.Email
        if not target_email:
            user_auth = User_Authentication.objects.filter(KhachHang=ve.KhachHang).first()
            target_email = user_auth.email if user_auth else None
        
        if not target_email: return False

        # Chọn template và tiêu đề
        if loai == 'booking':
            template_name = 'emails/booking_success.html'
            subject = f"[VexeApp] Thông báo đặt vé thành công - #{ve.VeID}"
        else:
            template_name = 'emails/payment_success.html'
            subject = f"[VexeApp] Xác nhận thanh toán thành công - Mã vé: {ve.VeID}"

        # Tính toán dữ liệu gộp
        tong_tien = sum(v.GiaVe for v in danh_sach_ve)
        gia_ve_format = "{:,.0f}".format(tong_tien).replace(',', '.')
        ma_ghe = ", ".join([v.Ghe.soGhe for v in danh_sach_ve if v.Ghe]) or "N/A"
        
        html_content = render_to_string(template_name, {
            've': ve,
            'danh_sach_ve': danh_sach_ve,
            'ma_ghe': ma_ghe,
            'gia_ve_format': gia_ve_format,
            'tong_so_ve': len(danh_sach_ve)
        })
        
        email = EmailMessage(subject, html_content, settings.DEFAULT_FROM_EMAIL, [target_email])
        email.content_subtype = "html"
        email.send(fail_silently=True)
        return True
    except Exception as e:
        print(f"Lỗi gửi mail {loai}: {e}")
        return False

def xu_ly_thanh_toan(request, ve_id):
    ve = get_object_or_404(Ve, pk=ve_id)
    nhaxe = ve.ChuyenXe.TuyenXe.nhaXe
    thanh_toan_online_kha_dung = all([nhaxe.MaNganHang, nhaxe.SoTaiKhoan])
    
    # Tìm các vé khác cùng ChuyenXe, cùng KhachHang, cùng trạng thái "Chưa thanh toán" 
    # được đặt cùng thời điểm (sai lệch tối đa 30 giây) để thanh toán gộp
    tu_ngay = ve.NgayDat - timezone.timedelta(seconds=30)
    den_ngay = ve.NgayDat + timezone.timedelta(seconds=30)
    
    danh_sach_ve = Ve.objects.filter(
        KhachHang=ve.KhachHang,
        ChuyenXe=ve.ChuyenXe,
        NgayDat__range=(tu_ngay, den_ngay)
    ).exclude(TrangThaiThanhToan="Đã thanh toán").exclude(TrangThai="Đã hủy")
    
    tong_so_ve = danh_sach_ve.count()
    tong_tien = sum(v.GiaVe for v in danh_sach_ve)
    danh_sach_ghe = ", ".join([v.Ghe.soGhe for v in danh_sach_ve if v.Ghe])
    
    # Lấy thông tin ngân hàng admin động
    admin_bank = lay_ngan_hang_admin()
    
    qr_url = None
    if thanh_toan_online_kha_dung:
        # Nội dung thanh toán bao gồm danh sách mã vé hoặc mã vé đầu tiên đại diện
        noi_dung = f"THANH TOAN VE {ve.VeID}"
        if tong_so_ve > 1:
            noi_dung = f"THANH TOAN {tong_so_ve} VE {ve.VeID}"
            
        qr_url = f"https://img.vietqr.io/image/{admin_bank['ma_ngan_hang']}-{admin_bank['so_tai_khoan']}-compact.png?amount={int(2000)}&addInfo={noi_dung}&accountName={admin_bank['ten_chu_tai_khoan']}"
    
    return render(request, 'khachhang/thanhtoan.html', {
        've': ve, 
        'danh_sach_ve': danh_sach_ve,
        'danh_sach_ghe': danh_sach_ghe,
        'tong_so_ve': tong_so_ve,
        'tong_tien': tong_tien,
        'qr_url': qr_url, 
        'thanh_toan_online_kha_dung': thanh_toan_online_kha_dung, 
        'thong_tin_ngan_hang': admin_bank
    })

def xac_nhan_thanh_toan(request, ve_id):
    if request.method == 'POST':
        ve = get_object_or_404(Ve, pk=ve_id)
        phuong_thuc = request.POST.get('phuong_thuc')
        
        # Tìm các vé liên quan để cập nhật gộp
        tu_ngay = ve.NgayDat - timezone.timedelta(seconds=30)
        den_ngay = ve.NgayDat + timezone.timedelta(seconds=30)
        danh_sach_ve = Ve.objects.filter(
            KhachHang=ve.KhachHang,
            ChuyenXe=ve.ChuyenXe,
            NgayDat__range=(tu_ngay, den_ngay)
        ).exclude(TrangThaiThanhToan="Đã thanh toán").exclude(TrangThai="Đã hủy")

        if phuong_thuc == 'Tiền mặt':
            danh_sach_ve.update(TrangThaiThanhToan="Chưa thanh toán")
        else:
            for v in danh_sach_ve:
                ThanhToan.objects.get_or_create(
                    Ve=v, 
                    defaults={
                        'ThanhToanID': tao_ma_thanh_toan_tu_dong(), 
                        'SoTien': v.GiaVe, 
                        'NgayThanhToan': timezone.now(), 
                        'DaQuyetToan': False
                    }
                )
            danh_sach_ve.update(TrangThaiThanhToan="Chưa thanh toán")
            messages.success(request, "Vui lòng chuyển khoản để hoàn tất.")
        return redirect('quanlyve')
    return redirect('quanlyve')

@csrf_exempt
def webhook_sepay(request):
    try:
        du_lieu = json.loads(request.body)
        noi_dung = du_lieu.get('content', '') or du_lieu.get('transaction_content', '')
        khop = re.search(r'VE\d+', noi_dung.upper())
        if khop:
            ve_goc = Ve.objects.filter(VeID=khop.group(0)).first()
            if ve_goc:
                # Tìm các vé đi kèm
                tu_ngay = ve_goc.NgayDat - timezone.timedelta(seconds=30)
                den_ngay = ve_goc.NgayDat + timezone.timedelta(seconds=30)
                danh_sach_ve = Ve.objects.filter(
                    KhachHang=ve_goc.KhachHang,
                    ChuyenXe=ve_goc.ChuyenXe,
                    NgayDat__range=(tu_ngay, den_ngay)
                ).exclude(TrangThaiThanhToan="Đã thanh toán").exclude(TrangThai="Đã hủy")

                ve_vua_thanh_toan = []
                for v in danh_sach_ve:
                    v.TrangThaiThanhToan = "Đã thanh toán"
                    v.save()
                    ThanhToan.objects.update_or_create(
                        Ve=v, 
                        defaults={
                            'ThanhToanID': tao_ma_thanh_toan_tu_dong() if not hasattr(v, 'thanhtoan') else v.thanhtoan.ThanhToanID, 
                            'SoTien': v.GiaVe, 
                            'NgayThanhToan': timezone.now(), 
                            'DaQuyetToan': False
                        }
                    )
                    ve_vua_thanh_toan.append(v)
                
                # Gửi duy nhất 1 mail XÁC NHẬN THANH TOÁN cho cả nhóm vé
                if ve_vua_thanh_toan:
                    gui_mail_ve(ve_vua_thanh_toan[0], loai='payment', danh_sach_ve=ve_vua_thanh_toan)
                
                return JsonResponse({'status': 'success'})
    except: pass
    return JsonResponse({'status': 'error'})

def kiem_tra_trang_thai_thanh_toan(request, ve_id):
    ve = Ve.objects.filter(VeID=ve_id).first()
    return JsonResponse({'da_thanh_toan': (ve.TrangThaiThanhToan == "Đã thanh toán") if ve else False})

def nhaxe_bao_cao_doanh_thu(request):
    user_id = request.session.get('user_id')
    if not user_id: return redirect('dangnhap')
    user_auth = User_Authentication.objects.filter(UserID=user_id).first()
    if not user_auth or user_auth.Vaitro != 'Nhaxe': return redirect('index')
    nhaxe = user_auth.Nhaxe
    if not nhaxe: nhaxe = Nhaxe.objects.filter(Email=user_auth.username).first()
    if not nhaxe: return redirect('index')
    giao_dich_cho_duyet = ThanhToan.objects.filter(Ve__ChuyenXe__TuyenXe__nhaXe=nhaxe, Ve__TrangThaiThanhToan="Đã thanh toán", DaQuyetToan=False).select_related('Ve').order_by('-NgayThanhToan')
    giao_dich_da_xong = ThanhToan.objects.filter(Ve__ChuyenXe__TuyenXe__nhaXe=nhaxe, Ve__TrangThaiThanhToan="Đã thanh toán", DaQuyetToan=True).select_related('Ve').order_by('-NgayThanhToan')
    tong_doanh_thu = sum(p.SoTien for p in giao_dich_cho_duyet)
    ti_le = Decimal(str(getattr(nhaxe, 'PhanTramHoaHong', 10.0) or 10.0)) / Decimal('100')
    tong_hoa_hong = Decimal(str(tong_doanh_thu)) * ti_le
    thuc_nhan = Decimal(str(tong_doanh_thu)) - tong_hoa_hong
    return render(request, 'nhaxe/bao_cao_doanh_thu.html', {'nha_xe': nhaxe, 'danh_sach_cho_duyet': giao_dich_cho_duyet, 'danh_sach_da_xong': giao_dich_da_xong, 'tong_doanh_thu': tong_doanh_thu, 'tong_hoa_hong': tong_hoa_hong, 'thuc_nhan': thuc_nhan})

def nhaxe_cau_hinh_ngan_hang(request):
    user_id = request.session.get('user_id')
    user_auth = User_Authentication.objects.filter(UserID=user_id).first()
    if not user_auth or user_auth.Vaitro != 'Nhaxe': return redirect('index')
    nhaxe = user_auth.Nhaxe
    if not nhaxe: nhaxe = Nhaxe.objects.filter(Email=user_auth.username).first()
    if not nhaxe: return redirect('index')
    if request.method == 'POST':
        nhaxe.MaNganHang = request.POST.get('ma_ngan_hang')
        nhaxe.SoTaiKhoan = request.POST.get('so_tai_khoan')
        nhaxe.TenChuTaiKhoan = request.POST.get('ten_chu_tai_khoan', '').upper()
        nhaxe.save()
        messages.success(request, "Cập nhật thành công!")
    return render(request, 'nhaxe/cau_hinh_ngan_hang.html', {
        'nhaxe': nhaxe,
        'nha_xe': nhaxe,
        'danh_sach_ngan_hang': DANH_SACH_NGAN_HANG
    })

# ==================== PHẦN DÀNH CHO ADMIN TỔNG ====================

def admin_kiem_tra_quyen(request):
    """Hàm bổ trợ kiểm tra quyền Admin"""
    user_id = request.session.get('user_id')
    user_auth = User_Authentication.objects.filter(UserID=user_id).first()
    if not user_auth or user_auth.Vaitro != 'Admin':
        return None
    return user_auth

def admin_bang_dieu_khien_quyet_toan(request):
    admin = admin_kiem_tra_quyen(request)
    if not admin: return redirect('dangnhap')
    
    bao_cao_nhaxe = []
    cac_nhaxe = Nhaxe.objects.all()
    
    for nx in cac_nhaxe:
        giao_dich_cho = ThanhToan.objects.filter(
            Ve__ChuyenXe__TuyenXe__nhaXe=nx, 
            DaQuyetToan=False, 
            Ve__TrangThaiThanhToan="Đã thanh toán"
        )
        
        if giao_dich_cho.exists():
            tong_tien = sum(t.SoTien for t in giao_dich_cho)
            ti_le = Decimal(str(getattr(nx, 'PhanTramHoaHong', 10.0) or 10.0)) / Decimal('100')
            thuc_nhan = Decimal(str(tong_tien)) * (1 - ti_le)
            
            bao_cao_nhaxe.append({
                'nhaxe': nx,
                'so_giao_dich': giao_dich_cho.count(),
                'thuc_nhan': thuc_nhan
            })
    
    return render(request, 'admin/quan_ly_quyet_toan.html', {'bao_cao_nhaxe': bao_cao_nhaxe})

def admin_xac_nhan_quyet_toan(request, nhaxe_id):
    admin = admin_kiem_tra_quyen(request)
    if not admin: return redirect('dangnhap')
    
    nx = get_object_or_404(Nhaxe, pk=nhaxe_id)
    
    # 1. Lọc giao dịch chưa quyết toán
    giao_dich_cho = ThanhToan.objects.filter(
        Ve__ChuyenXe__TuyenXe__nhaXe=nx, 
        DaQuyetToan=False, 
        Ve__TrangThaiThanhToan="Đã thanh toán"
    )
    
    if not giao_dich_cho.exists():
        messages.warning(request, "Không có giao dịch nào cần quyết toán.")
        return redirect('admin_dashboard_quyet_toan')
        
    # 2. Tính toán số tiền để gửi mail
    tong_tien = sum(t.SoTien for t in giao_dich_cho)
    ti_le = Decimal(str(getattr(nx, 'PhanTramHoaHong', 10.0) or 10.0)) / Decimal('100')
    thuc_nhan = Decimal(str(tong_tien)) * (1 - ti_le)
    so_luong = giao_dich_cho.count()

    # 3. Cập nhật trạng thái trong DB
    giao_dich_cho.update(DaQuyetToan=True)
    
    # 4. Gửi mail thông báo HTML cho nhà xe
    try:
        from django.core.mail import EmailMessage
        from django.conf import settings
        
        subject = f"[VexeApp] Thông báo quyết toán thành công - {nx.TenNhaXe}"
        
        # Định dạng tiền
        tong_tien_format = "{:,.0f}".format(tong_tien).replace(',', '.')
        hoa_hong_format = "{:,.0f}".format(tong_tien * ti_le).replace(',', '.')
        thuc_nhan_format = "{:,.0f}".format(thuc_nhan).replace(',', '.')
        
        html_content = render_to_string('emails/settlement_notification.html', {
            'nx': nx,
            'so_luong': so_luong,
            'tong_tien_format': tong_tien_format,
            'hoa_hong_format': hoa_hong_format,
            'thuc_nhan_format': thuc_nhan_format
        })
        
        email = EmailMessage(subject, html_content, settings.DEFAULT_FROM_EMAIL, [nx.Email])
        email.content_subtype = "html"
        email.send(fail_silently=True)
    except Exception as e:
        print(f"Lỗi gửi mail quyết toán: {e}")

    messages.success(request, f"Đã quyết toán và gửi mail thông báo cho nhà xe {nx.TenNhaXe}")
    return redirect('admin_dashboard_quyet_toan')

def admin_danh_sach_nhaxe(request):
    admin = admin_kiem_tra_quyen(request)
    if not admin: return redirect('dangnhap')
    
    danh_sach = Nhaxe.objects.all().order_by('NhaxeID')
    return render(request, 'admin/list_nhaxe.html', {'danh_sach_nhaxe': danh_sach})

def admin_danh_sach_khachhang(request):
    admin = admin_kiem_tra_quyen(request)
    if not admin: return redirect('dangnhap')
    
    danh_sach = KhachHang.objects.all().order_by('KhachHangID')
    # Gán thêm SĐT từ bảng User_Authentication cho từng khách hàng
    for kh in danh_sach:
        user_auth = User_Authentication.objects.filter(KhachHang=kh).first()
        kh.SDT = user_auth.SoDienThoai if user_auth else "Chưa có"
        
    return render(request, 'admin/list_khachhang.html', {'danh_sach_khachhang': danh_sach})


def admin_cau_hinh_ngan_hang(request):
    admin = admin_kiem_tra_quyen(request)
    if not admin: return redirect('dangnhap')
    
    cau_hinh = NganHangAdmin.objects.first()
    
    if request.method == 'POST':
        ten_chu = request.POST.get('ten_chu_tai_khoan', '').upper()
        ma_nh = request.POST.get('ma_ngan_hang')
        so_tk = request.POST.get('so_tai_khoan')
        
        if cau_hinh:
            cau_hinh.TenChuTaiKhoan = ten_chu
            cau_hinh.MaNganHang = ma_nh
            cau_hinh.SoTaiKhoan = so_tk
            cau_hinh.save()
        else:
            NganHangAdmin.objects.create(
                TenChuTaiKhoan=ten_chu,
                MaNganHang=ma_nh,
                SoTaiKhoan=so_tk
            )
        messages.success(request, "Cấu hình ngân hàng Admin đã được cập nhật!")
        return redirect('admin_cau_hinh_ngan_hang')

    return render(request, 'admin/cau_hinh_ngan_hang.html', {
        'cau_hinh': cau_hinh,
        'danh_sach_ngan_hang': DANH_SACH_NGAN_HANG
    })
