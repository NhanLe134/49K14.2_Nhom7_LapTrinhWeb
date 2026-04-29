from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Ve, ThanhToan, Nhaxe, User_Authentication, KhachHang
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
import re
from decimal import Decimal

# Thông tin tài khoản Admin
NGAN_HANG_ADMIN = {
    'ma_ngan_hang': 'MB',
    'so_tai_khoan': '0352149424',
    'ten_chu_tai_khoan': 'DANG NGOC ANH THU'
}

def tao_ma_thanh_toan_tu_dong():
    last_tt = ThanhToan.objects.all().order_by('ThanhToanID').last()
    if not last_tt: return "TT0001"
    match = re.search(r'\d+', last_tt.ThanhToanID)
    next_id = int(match.group()) + 1 if match else 1
    return f"TT{next_id:04d}"

def xu_ly_thanh_toan(request, ve_id):
    ve = get_object_or_404(Ve, pk=ve_id)
    nhaxe = ve.ChuyenXe.TuyenXe.nhaXe
    thanh_toan_online_kha_dung = all([nhaxe.MaNganHang, nhaxe.SoTaiKhoan])
    qr_url = None
    if thanh_toan_online_kha_dung:
        so_tien = 2000 # Dùng 2000đ để test thực tế
        noi_dung = f"THANH TOAN VE {ve.VeID}"
        qr_url = f"https://img.vietqr.io/image/{NGAN_HANG_ADMIN['ma_ngan_hang']}-{NGAN_HANG_ADMIN['so_tai_khoan']}-compact.png?amount={so_tien}&addInfo={noi_dung}&accountName={NGAN_HANG_ADMIN['ten_chu_tai_khoan']}"
    return render(request, 'khachhang/payment.html', {'ve': ve, 'qr_url': qr_url, 'thanh_toan_online_kha_dung': thanh_toan_online_kha_dung, 'thong_tin_ngan_hang': NGAN_HANG_ADMIN})

def xac_nhan_thanh_toan(request, ve_id):
    if request.method == 'POST':
        ve = get_object_or_404(Ve, pk=ve_id)
        phuong_thuc = request.POST.get('phuong_thuc')
        if phuong_thuc == 'Tiền mặt':
            ve.TrangThaiThanhToan = "Chưa thanh toán (Tiền mặt)"
            ve.save()
        else:
            ThanhToan.objects.get_or_create(Ve=ve, defaults={'ThanhToanID': tao_ma_thanh_toan_tu_dong(), 'SoTien': ve.GiaVe, 'NgayThanhToan': timezone.now(), 'DaQuyetToan': False})
            ve.TrangThaiThanhToan = "Chờ xác nhận"
            ve.save()
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
            ve = Ve.objects.filter(VeID=khop.group(0)).first()
            if ve:
                ve.TrangThaiThanhToan = "Đã thanh toán"
                ve.save()
                ThanhToan.objects.update_or_create(Ve=ve, defaults={'ThanhToanID': tao_ma_thanh_toan_tu_dong() if not hasattr(ve, 'thanhtoan') else ve.thanhtoan.ThanhToanID, 'SoTien': du_lieu.get('transfer_amount', 0), 'NgayThanhToan': timezone.now(), 'DaQuyetToan': False})
                return JsonResponse({'status': 'success'})
    except: pass
    return JsonResponse({'status': 'error'})

def kiem_tra_trang_thai_thanh_toan(request, ve_id):
    ve = Ve.objects.filter(VeID=ve_id).first()
    return JsonResponse({'da_thanh_toan': (ve.TrangThaiThanhToan == "Đã thanh toán") if ve else False})

def khachhang_lich_su_giao_dich(request):
    user_id = request.session.get('user_id')
    user_auth = User_Authentication.objects.filter(UserID=user_id).first()
    if not user_auth or user_auth.Vaitro != 'KhachHang': return redirect('dangnhap')
    danh_sach = ThanhToan.objects.filter(Ve__KhachHang=user_auth.KhachHang).order_by('-NgayThanhToan')
    return render(request, 'khachhang/transactions.html', {'danh_sach_giao_dich': danh_sach})

def nhaxe_bao_cao_doanh_thu(request):
    user_id = request.session.get('user_id')
    if not user_id: return redirect('dangnhap')
    user_auth = User_Authentication.objects.filter(UserID=user_id).first()
    if not user_auth or user_auth.Vaitro != 'Nhaxe': return redirect('index')
    nhaxe = user_auth.Nhaxe
    if not nhaxe: nhaxe = Nhaxe.objects.filter(Email=user_auth.TenDangNhap).first()
    if not nhaxe: return redirect('index')
    giao_dich_cho_duyet = ThanhToan.objects.filter(Ve__ChuyenXe__TuyenXe__nhaXe=nhaxe, Ve__TrangThaiThanhToan="Đã thanh toán", DaQuyetToan=False).select_related('Ve').order_by('-NgayThanhToan')
    giao_dich_da_xong = ThanhToan.objects.filter(Ve__ChuyenXe__TuyenXe__nhaXe=nhaxe, Ve__TrangThaiThanhToan="Đã thanh toán", DaQuyetToan=True).select_related('Ve').order_by('-NgayThanhToan')
    tong_doanh_thu = sum(p.SoTien for p in giao_dich_cho_duyet)
    ti_le = Decimal(str(getattr(nhaxe, 'PhanTramHoaHong', 10.0) or 10.0)) / Decimal('100')
    tong_hoa_hong = Decimal(str(tong_doanh_thu)) * ti_le
    thuc_nhan = Decimal(str(tong_doanh_thu)) - tong_hoa_hong
    return render(request, 'nhaxe/revenue_report.html', {'nhaxe': nhaxe, 'danh_sach_cho_duyet': giao_dich_cho_duyet, 'danh_sach_da_xong': giao_dich_da_xong, 'tong_doanh_thu': tong_doanh_thu, 'tong_hoa_hong': tong_hoa_hong, 'thuc_nhan': thuc_nhan})

def nhaxe_cau_hinh_ngan_hang(request):
    user_id = request.session.get('user_id')
    user_auth = User_Authentication.objects.filter(UserID=user_id).first()
    if not user_auth or user_auth.Vaitro != 'Nhaxe': return redirect('index')
    nhaxe = user_auth.Nhaxe
    if not nhaxe: nhaxe = Nhaxe.objects.filter(Email=user_auth.TenDangNhap).first()
    if not nhaxe: return redirect('index')
    if request.method == 'POST':
        nhaxe.MaNganHang = request.POST.get('ma_ngan_hang')
        nhaxe.SoTaiKhoan = request.POST.get('so_tai_khoan')
        nhaxe.TenChuTaiKhoan = request.POST.get('ten_chu_tai_khoan', '').upper()
        nhaxe.save()
        messages.success(request, "Cập nhật thành công!")
    return render(request, 'nhaxe/bank_config.html', {'nhaxe': nhaxe})
