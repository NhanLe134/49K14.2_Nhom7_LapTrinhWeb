from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from .models import ChuyenXe, GheNgoi, Ve, User_Authentication, KhachHang
import uuid

# ==================== ĐIỀN THÔNG TIN VÀ XÁC NHẬN ĐẶT VÉ ====================

def dat_ve_thong_tin(request):
    """
    Hàm View Bước 1: Hiển thị form điền thông tin khách hàng và chọn điểm đón/trả trên bản đồ.
    Nhận chuyen_id và danh sách ghe_ids từ tham số GET.
    """
    try:
        chuyen_id = request.GET.get('chuyen_id')
        # Lấy danh sách ghế đang chọn từ tham số URL hoặc session
        # Ví dụ: ?ghe_ids=G01&ghe_ids=G02
        ghe_ids = request.GET.getlist('ghe_ids')

        if not chuyen_id or not ghe_ids:
            messages.warning(request, "Vui lòng chọn chuyến xe và chỗ ngồi trước.")
            return redirect('timkiem')

        # Lấy dữ liệu thực tế từ ChuyenXe
        chuyen_xe = ChuyenXe.objects.select_related('TuyenXe', 'Xe__Loaixe').get(ChuyenXeID=chuyen_id)

        context = {
            'chuyen_xe': chuyen_xe,
            'chuyen_id': chuyen_id,
            'ghe_ids': ghe_ids,
            'so_luong': len(ghe_ids),
        }

        # Kiểm tra session xem khách đã đăng nhập chưa để pre-fill form
        user_id = request.session.get('user_id')
        if user_id:
            auth_user = User_Authentication.objects.filter(UserID=user_id).first()
            if auth_user and auth_user.KhachHang:
                # Query lấy dữ liệu khách hàng để truyền ra context
                context['khach_hang'] = auth_user.KhachHang
                context['sdt_mac_dinh'] = auth_user.SoDienThoai

        return render(request, 'home/dien_thong_tin_ve.html', context)

    except Exception as e:
        messages.error(request, f"Lỗi hệ thống: {str(e)}")
        return redirect('index')


def xac_nhan_dat_ve(request):
    """
    Hàm View Bước 2: Xử lý request POST khi khách xác nhận đặt vé.
    Lưu thông tin vé và cập nhật trạng thái ghế ngồi.
    """
    if request.method == 'POST':
        try:
            chuyen_id = request.POST.get('chuyen_id')
            ghe_ids = request.POST.getlist('ghe_ids')
            ho_ten = request.POST.get('ho_ten')
            sdt = request.POST.get('sdt')
            diem_don = request.POST.get('diem_don')
            diem_tra = request.POST.get('diem_tra')

            # Kiểm tra đăng nhập (Bắt buộc để liên kết vé với Khách hàng)
            user_id = request.session.get('user_id')
            if not user_id:
                messages.error(request, "Vui lòng đăng nhập để thực hiện đặt vé.")
                return redirect('dangnhap')

            auth_user = User_Authentication.objects.get(UserID=user_id)
            khach_hang = auth_user.KhachHang
            
            if not khach_hang:
                messages.error(request, "Tài khoản của bạn không có thông tin khách hàng.")
                return redirect('index')

            chuyen_xe = ChuyenXe.objects.get(ChuyenXeID=chuyen_id)

            # 0. Lấy mã VeID lớn nhất hiện tại để làm căn cứ tăng dần
            all_ve_ids = Ve.objects.values_list('VeID', flat=True)
            max_num = 0
            for v_id in all_ve_ids:
                if v_id and v_id.startswith('VE') and v_id[2:].isdigit():
                    num = int(v_id[2:])
                    if num > max_num: max_num = num

            # Quét qua danh sách ghế đã chọn và tạo vé
            for index, ghe_id in enumerate(ghe_ids):
                # 0. Đảm bảo ghế tồn tại trong DB (nếu chưa có thì tạo mới)
                ghe, created = GheNgoi.objects.get_or_create(
                    soGhe=ghe_id, 
                    ChuyenXe=chuyen_xe,
                    defaults={'gheID': f"G{chuyen_id[2:]}{ghe_id}", 'trangThai': 'Còn trống'}
                )
                
                # 0.1 Tính mã VeID tự động (Tăng dần theo index)
                ve_id = f"VE{max_num + index + 1:04d}"
                
                # 1. Tạo mới bản ghi Ve
                Ve.objects.create(
                    VeID=ve_id,
                    KhachHang=khach_hang,
                    ChuyenXe=chuyen_xe,
                    Ghe=ghe,
                    SoDienThoai=sdt,
                    HoTen=ho_ten,
                    DiemDon=diem_don,
                    DiemTra=diem_tra,
                    GiaVe=chuyen_xe.Xe.Loaixe.GiaVe, # Lấy giá niêm yết từ Loại xe
                    TrangThaiThanhToan="Chưa thanh toán" # Ràng buộc: Luôn là Chưa thanh toán khi mới tạo
                )

                # 2. Đổi trạng thái ghế thành "Đã đặt"
                ghe.trangThai = "Đã đặt"
                ghe.save()

            messages.success(request, f"Chúc mừng! Bạn đã đặt thành công {len(ghe_ids)} vé.")
            return redirect('quanlyve') # Điều hướng về trang quản lý vé của tôi

        except Exception as e:
            messages.error(request, f"Đặt vé thất bại: {str(e)}")
            return redirect('timkiem')

    return redirect('index')

def huy_ve(request, ve_id):
    """
    Hàm xử lý hủy vé: Cập nhật trạng thái vé thành 'Đã hủy' và chuyển trạng thái ghế sang 'Còn trống'.
    """
    try:
        # Lấy bản ghi vé
        ve = get_object_or_404(Ve, VeID=ve_id)
        
        # Lấy ghế liên quan để giải phóng
        ghe = ve.Ghe
        if ghe:
            ghe.trangThai = "Còn trống"
            ghe.save()
            
        # Cập nhật trạng thái vé thay vì xóa
        ve.TrangThai = "Đã hủy"
        ve.TrangThaiThanhToan = "Đã hủy"
        ve.save()
        
        return JsonResponse({'status': 'success', 'message': 'Hủy vé thành công và đã giải phóng chỗ.'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})
