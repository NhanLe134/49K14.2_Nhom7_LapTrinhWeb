from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Ve, ThanhToan
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
import re

def process_payment(request, ve_id):
    """Trang hiển thị lựa chọn thanh toán cho một Vé."""
    ve = get_object_or_404(Ve, pk=ve_id)
    
    # Lấy thông tin nhà xe từ chuyến xe của vé
    nhaxe = ve.ChuyenXe.TuyenXe.nhaXe
    
    # Thông tin tài khoản nhận tiền
    BANK_ID = nhaxe.MaNganHang 
    ACCOUNT_NO = nhaxe.SoTaiKhoan
    ACCOUNT_NAME = nhaxe.TenChuTaiKhoan 
    
    # Kiểm tra xem nhà xe đã thiết lập đủ thông tin thanh toán chưa
    online_payment_available = all([BANK_ID, ACCOUNT_NO, ACCOUNT_NAME])
    
    # Nếu chưa thiết lập đủ, ta không tạo link QR
    qr_url = None
    if online_payment_available:
        # Tạm thời để 2000 để bạn test cho rẻ, sau này đổi lại thành ve.GiaVe
        AMOUNT = 2000 
        description = f"THANH TOAN VE {ve.VeID}"
        qr_url = f"https://img.vietqr.io/image/{BANK_ID}-{ACCOUNT_NO}-compact.png?amount={AMOUNT}&addInfo={description}&accountName={ACCOUNT_NAME}"

    return render(request, 'khachhang/payment.html', {
        've': ve,
        'qr_url': qr_url,
        'online_payment_available': online_payment_available,
        'bank_info': {
            'bank_id': BANK_ID,
            'account_no': ACCOUNT_NO,
            'account_name': ACCOUNT_NAME
        }
    })

def confirm_payment(request, ve_id):
    """Xử lý khi người dùng nhấn xác nhận thanh toán."""
    if request.method == 'POST':
        ve = get_object_or_404(Ve, pk=ve_id)
        phuong_thuc = request.POST.get('phuong_thuc')
        
        # Nếu là Tiền mặt: Không đổi gì trong DB, quay về trang quản lý vé
        if phuong_thuc == 'Tiền mặt':
            return redirect('quanlyve')

        # Nếu là Chuyển khoản: Cập nhật trạng thái chờ xác nhận (Xử lý Offline/Manual)
        # (Lưu ý: Nếu dùng SePay tự động thì luồng này thường dành cho khách nhấn xác nhận thủ công)
        payment_record, created = ThanhToan.objects.update_or_create(
            Ve=ve,
            defaults={
                'SoTien': ve.GiaVe,
                'PhuongThucTT': phuong_thuc,
                'NgayThanhToan': timezone.now(),
                'MaGiaoDich': f"GIAODICH_{ve.VeID}"
            }
        )

        if created:
            last_tt = ThanhToan.objects.all().exclude(ThanhToanID=payment_record.ThanhToanID).order_by('ThanhToanID').last()
            num = 1
            if last_tt:
                import re
                match = re.search(r'\d+', last_tt.ThanhToanID)
                if match: num = int(match.group()) + 1
            payment_record.ThanhToanID = f"TT{num:04d}"
            payment_record.save()

        ve.TrangThaiThanhToan = "Đã thanh toán (Chờ xác nhận)"
        ve.save()
        
        messages.success(request, "Vui lòng thực hiện chuyển khoản theo thông tin bên dưới.")
        return redirect('quanlyve')

    return redirect('khachhang')

def check_payment_status(request, ve_id):
    """API để frontend check xem vé đã thanh toán chưa."""
    ve = get_object_or_404(Ve, pk=ve_id)
    return JsonResponse({
        'paid': ve.TrangThaiThanhToan == "Đã thanh toán",
        'status': ve.TrangThaiThanhToan
    })

@csrf_exempt
def sepay_webhook(request):
    """
    Webhook nhận thông báo từ SePay.vn
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Only POST allowed'}, status=405)

    try:
        data = json.loads(request.body)
        print("\n--- NHẬN WEBHOOK TỪ SEPAY ---")
        print(f"Dữ liệu thô: {data}")
        
        # Lấy nội dung chuyển khoản
        content = data.get('content', '') or data.get('transaction_content', '')
        amount = data.get('transfer_amount', 0) or data.get('amount_in', 0)
        
        print(f"Nội dung: {content}, Số tiền: {amount}")

        # Tìm mã vé (Regex VE + số)
        match = re.search(r'VE\d+', content.upper())
        if not match:
            print("LỖI: Không tìm thấy mã VE trong nội dung chuyển khoản")
            return JsonResponse({'status': 'error', 'message': 'Ticket code (VE...) not found in content'}, status=200)

        ve_id = match.group(0)
        print(f"Tìm thấy VeID: {ve_id}")
        
        ve = Ve.objects.filter(VeID=ve_id).first()

        if not ve:
            print(f"LỖI: Không tìm thấy vé {ve_id} trong database")
            return JsonResponse({'status': 'error', 'message': f'Ticket {ve_id} not found'}, status=200)

        # Nếu vé đã thanh toán rồi thì thôi
        if ve.TrangThaiThanhToan == "Đã thanh toán":
            print(f"Vé {ve_id} đã được cập nhật trước đó.")
            return JsonResponse({'status': 'success', 'message': 'Already paid'}, status=200)

        # Cập nhật trạng thái vé
        ve.TrangThaiThanhToan = "Đã thanh toán"
        ve.save()
        print(f"Đã cập nhật trạng thái Vé {ve_id} thành 'Đã thanh toán'")

        # Tạo bản ghi ThanhToan
        payment_record, created = ThanhToan.objects.update_or_create(
            Ve=ve,
            defaults={
                'SoTien': amount,
                'PhuongThucTT': 'Chuyển khoản (SePay)',
                'NgayThanhToan': timezone.now(),
                'MaGiaoDich': data.get('reference_number', f"SEPAY_{data.get('id')}")
            }
        )

        # Gán ID nếu là tạo mới (TTxxxx)
        if created:
            last_tt = ThanhToan.objects.all().exclude(ThanhToanID=payment_record.ThanhToanID).order_by('ThanhToanID').last()
            num = 1
            if last_tt:
                m = re.search(r'\d+', last_tt.ThanhToanID)
                if m: num = int(m.group()) + 1
            payment_record.ThanhToanID = f"TT{num:04d}"
            payment_record.save()
            print(f"Đã tạo bản ghi thanh toán {payment_record.ThanhToanID}")

        return JsonResponse({'status': 'success', 'message': f'Ticket {ve_id} updated to Paid'}, status=200)

    except Exception as e:
        print(f"LỖI XỬ LÝ WEBHOOK: {str(e)}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=200)
