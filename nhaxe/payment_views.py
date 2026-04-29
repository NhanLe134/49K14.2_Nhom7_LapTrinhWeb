from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Ve, ThanhToan
from django.utils import timezone

def process_payment(request, ve_id):
    """Trang hiển thị lựa chọn thanh toán cho một Vé."""
    ve = get_object_or_404(Ve, pk=ve_id)
    
    # Thông tin tài khoản nhận tiền của bạn
    BANK_ID = "MB" 
    ACCOUNT_NO = "0377400632"
    ACCOUNT_NAME = "NHAN LE" # Bạn có thể đổi tên này cho đúng
    
    # Tạo link VietQR tự động
    # Format: https://img.vietqr.io/image/<BANK_ID>-<ACCOUNT_NO>-template.png?amount=<AMOUNT>&addInfo=<DESCRIPTION>&accountName=<NAME>
    description = f"THANH TOAN VE {ve.VeID}"
    qr_url = f"https://img.vietqr.io/image/{BANK_ID}-{ACCOUNT_NO}-compact.png?amount={ve.GiaVe}&addInfo={description}&accountName={ACCOUNT_NAME}"

    return render(request, 'khachhang/payment.html', {
        've': ve,
        'qr_url': qr_url
    })

def confirm_payment(request, ve_id):
    """Xử lý khi người dùng nhấn xác nhận thanh toán."""
    if request.method == 'POST':
        ve = get_object_or_404(Ve, pk=ve_id)
        phuong_thuc = request.POST.get('phuong_thuc')
        
        # 1. Cập nhật hoặc Tạo bản ghi ThanhToan (Dùng update_or_create để tránh lỗi trùng lặp One-to-One)
        payment_record, created = ThanhToan.objects.update_or_create(
            Ve=ve,
            defaults={
                'SoTien': ve.GiaVe,
                'PhuongThucTT': phuong_thuc,
                'NgayThanhToan': timezone.now(),
                'MaGiaoDich': f"GIAODICH_{ve.VeID}"
            }
        )

        # Chỉ khi tạo mới hoàn toàn bản ghi ThanhToan, ta mới gán ID mới theo mẫu TTxxxx
        if created:
            last_tt = ThanhToan.objects.all().exclude(ThanhToanID=payment_record.ThanhToanID).order_by('ThanhToanID').last()
            num = 1
            if last_tt:
                import re
                match = re.search(r'\d+', last_tt.ThanhToanID)
                if match: num = int(match.group()) + 1
            payment_record.ThanhToanID = f"TT{num:04d}"
            payment_record.save()

        # 2. Cập nhật trạng thái Vé
        if phuong_thuc == 'Chuyển khoản':
            ve.TrangThaiThanhToan = "Đã thanh toán (Chờ xác nhận)"
        else:
            ve.TrangThaiThanhToan = "Chờ thanh toán tiền mặt"
        
        ve.save()
        
        messages.success(request, "Thanh toán thành công! Vui lòng kiểm tra lại vé.")
        return redirect('vecuatoi') # Quay về trang Vé của tôi

    return redirect('khachhang')

def dat_ve(request):
    """Xử lý tạo vé mới từ yêu cầu đặt chỗ của khách hàng."""
    if request.method == 'POST':
        # Giả định bạn gửi các thông tin này lên từ Form đặt vé
        chuyenxe_id = request.POST.get('chuyenxe_id')
        ghe_id = request.POST.get('ghe_id') 
        khach_hang_id = request.session.get('user_id')
        
        if not khach_hang_id:
            messages.error(request, "Vui lòng đăng nhập để đặt vé.")
            return redirect('dangnhap')

        # Tạo mã vé tự động
        last_ve = Ve.objects.all().order_by('VeID').last()
        num = 1
        if last_ve:
            import re
            match = re.search(r'\d+', last_ve.VeID)
            if match: num = int(match.group()) + 1
        new_ve_id = f"VE{num:04d}"

        # Lấy thông tin chuyến xe để lấy giá vé
        chuyen = get_object_or_404(ChuyenXe, pk=chuyenxe_id)

        # Tạo vé mới
        ve_moi = Ve.objects.create(
            VeID=new_ve_id,
            KhachHang_id=khach_hang_id,
            ChuyenXe_id=chuyenxe_id,
            Ghe_id=ghe_id,
            SoDienThoai=request.POST.get('sdt', '0123456789'),
            GiaVe=450000, # Giả sử giá vé cố định hoặc lấy từ ChuyenXe
            TrangThaiThanhToan="Chưa thanh toán"
        )

        # Sau khi tạo vé xong -> Chuyển sang trang thanh toán luôn
        return redirect('process_payment', ve_id=ve_moi.VeID)

    return redirect('khachhang')
