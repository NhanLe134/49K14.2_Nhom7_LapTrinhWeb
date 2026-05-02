from .models import ChuyenXe, GheNgoi, CHITIETLOAIXE, TuyenXe, User_Authentication, Ve,KhachHang
from django.db.models import Q
from django.shortcuts import render
from django.contrib import messages
from django.http import JsonResponse


def tim_kiem_chuyen_xe_kha_dung(diem_di, diem_den, ngay_di):
    try:
        # Xây dựng bộ lọc động
        filters = Q()
        if diem_di:
            filters &= Q(TuyenXe__diemDi__icontains=diem_di)
        if diem_den:
            filters &= Q(TuyenXe__diemDen__icontains=diem_den)
        if ngay_di:
            filters &= Q(NgayKhoiHanh=ngay_di)

        # Lọc chuyến xe
        chuyen_xe_query = ChuyenXe.objects.filter(filters).exclude(TrangThai__in=['Hoàn thành', 'Đã hủy']) \
            .select_related('TuyenXe', 'Xe__Loaixe', 'Xe__Nhaxe', 'Taixe')

        danh_sach_ket_qua = []

        for cx in chuyen_xe_query:
            # KIỂM TRA AN TOÀN: Nếu chuyến xe chưa gán xe hoặc chưa có tuyến thì bỏ qua hoặc gán giá trị mặc định
            if not cx.Xe or not cx.TuyenXe:
                continue

                # 1. Lấy thông tin giá vé từ bảng CHITIETLOAIXE
            ct_loaixe = CHITIETLOAIXE.objects.filter(
                Nhaxe=cx.Xe.Nhaxe,
                Loaixe=cx.Xe.Loaixe
            ).first()

            # Xử lý tên loại xe hiển thị
            if ct_loaixe and ct_loaixe.TenLoaiXe:
                ten_loai = ct_loaixe.TenLoaiXe
            else:
                ten_loai = f"Xe {cx.Xe.Loaixe.SoCho} chỗ"

            # Lấy Giá vé thực tế (Ưu tiên giá riêng của nhà xe, fallback về giá chung của loại xe)
            gia_ve_thuc_te = 0
            if ct_loaixe and ct_loaixe.GiaVe > 0:
                gia_ve_thuc_te = ct_loaixe.GiaVe
            elif cx.Xe.Loaixe and cx.Xe.Loaixe.GiaVe > 0:
                gia_ve_thuc_te = cx.Xe.Loaixe.GiaVe

            # 2. Tính toán số chỗ trống (Dùng model Ve để chính xác tuyệt đối)
            tong_ghe_xe = cx.Xe.Loaixe.SoCho
            # Quy tắc trừ ghế tài xế của bạn
            if tong_ghe_xe == 4:
                tong_ghe_ban = 4
            elif tong_ghe_xe == 7:
                tong_ghe_ban = 7
            elif tong_ghe_xe == 9:
                tong_ghe_ban = 9
            else:
                tong_ghe_ban = max(0, tong_ghe_xe - 1)

            # Đếm số vé đã đặt cho chuyến này
            ve_da_dat_count = Ve.objects.filter(ChuyenXe=cx).exclude(TrangThai='Đã hủy').count()
            so_cho_trong = max(0, tong_ghe_ban - ve_da_dat_count)

            # 3. Tính toán đánh giá trung bình
            danh_gia_tb = 0
            if cx.Xe.Nhaxe.SoLuotDanhGia > 0:
                danh_gia_tb = round(cx.Xe.Nhaxe.TongDiemDanhGia / cx.Xe.Nhaxe.SoLuotDanhGia, 1)

            # 4. Đóng gói dữ liệu
            item = {
                'ChuyenXeID': cx.ChuyenXeID,
                'GioDi': cx.GioDi,
                'GioDen': cx.GioDen,
                'NgayKhoiHanh': cx.NgayKhoiHanh,
                'tenTuyen': cx.TuyenXe.tenTuyen,
                'DiemDi': cx.TuyenXe.diemDi,
                'DiemDen': cx.TuyenXe.diemDen,
                'GiaVe': gia_ve_thuc_te,
                'TenNhaXe': cx.Xe.Nhaxe.TenNhaXe,
                'LoaiXe': ten_loai,
                'BienSoXe': cx.Xe.BienSoXe,
                'TenTaiXe': cx.Taixe.HoTen if cx.Taixe else 'Chưa rõ',
                'SoChoTrong': so_cho_trong,
                'TongSoCho': tong_ghe_ban,
                'DanhGiaTB': danh_gia_tb,
                'SoLuotDanhGia': cx.Xe.Nhaxe.SoLuotDanhGia,
                'TrangThai': cx.TrangThai or 'Đang chờ'
            }
            danh_sach_ket_qua.append(item)

        return danh_sach_ket_qua

    except Exception as e:
        print(f"Lỗi truy vấn ChuyenXe: {str(e)}")
        return []
def lay_so_do_ghe(chuyen_xe_id):
    """
    Đã sửa lỗi logic so sánh chuỗi status để màu sắc hiển thị đúng trên Template
    """
    try:
        chuyen = ChuyenXe.objects.select_related('Xe__Loaixe').get(ChuyenXeID=chuyen_xe_id)
        tong_cho = chuyen.Xe.Loaixe.SoCho if chuyen.Xe and chuyen.Xe.Loaixe else 4

        if tong_cho == 4:
            prefix, count = "A", 4
        elif tong_cho == 7:
            prefix, count = "B", 7
        elif tong_cho == 9:
            prefix, count = "C", 9
        else:
            prefix, count = "S", tong_cho - 1

        labels = [f"{prefix}{i}" for i in range(1, count + 1)]
        ghe_db = GheNgoi.objects.filter(ChuyenXe=chuyen)

        # Chuẩn hóa trạng thái ghế từ DB
        ghe_status_map = {}
        for g in ghe_db:
            if g.soGhe:
                # Lưu vào map: "B1": "Đã đặt"
                ghe_status_map[str(g.soGhe).strip().upper()] = str(g.trangThai).strip()

        danh_sach_ghe = []
        for label in labels:
            db_status = ghe_status_map.get(label.upper(), "Còn trống")

            # Logic mapping màu sắc cho CSS của bạn
            # "Đã đặt" -> sold (màu xanh blue trong CSS của bạn)
            # "Còn trống" -> available
            if "đã đặt" in db_status.lower():
                final_status = "sold"
            else:
                final_status = "available"

            danh_sach_ghe.append({
                "soGhe": label,
                "trangThai": final_status
            })

        return danh_sach_ghe
    except Exception as e:
        return []
# ==================== VIEWS CHO TÌM KIẾM CHUYẾN XE ====================

def view_tim_kiem_ve(request):
    """
    View xử lý tìm kiếm chuyến xe dựa trên các tham số GET.
    """
    origin = request.GET.get('origin', '').strip()
    destination = request.GET.get('destination', '').strip()
    depart_date = request.GET.get('depart_date', '').strip()

    # Lấy thông tin khách hàng đang đăng nhập để pre-fill form
    user_id = request.session.get('user_id')
    khach_hang = None
    sdt_mac_dinh = ""
    if user_id:
        try:
            auth_user = User_Authentication.objects.get(UserID=user_id)
            khach_hang = auth_user.KhachHang
            sdt_mac_dinh = auth_user.SoDienThoai
        except User_Authentication.DoesNotExist:
            pass

    # Lấy tất cả các địa điểm duy nhất xuất hiện trong Database (cả điểm đi và điểm đến), lọc bỏ các giá trị rỗng
    try:
        diem_di_list = list(TuyenXe.objects.filter(diemDi__isnull=False).values_list('diemDi', flat=True).distinct())
        diem_den_list = list(TuyenXe.objects.filter(diemDen__isnull=False).values_list('diemDen', flat=True).distinct())
        # Gộp lại và sắp xếp
        vung_mien = sorted(list(set(diem_di_list + diem_den_list)))
        cac_diem_di = vung_mien
        cac_diem_den = vung_mien
    except:
        cac_diem_di = ['Đà Nẵng', 'Huế', 'Hội An']
        cac_diem_den = ['Đà Nẵng', 'Huế', 'Hội An']

    try:
        # Logic tìm kiếm mới:
        # 1. Nếu nhấn tìm kiếm mà TRỐNG TẤT CẢ các trường -> Áp dụng mặc định (Đà Nẵng - Huế - Hôm nay)
        # 2. Nếu có ít nhất một trường được nhập -> Tìm kiếm theo các trường đó
        search_submitted = request.GET.get('search_submitted') == '1'
        
        if search_submitted or origin or destination or depart_date:
            if search_submitted and not origin and not destination and not depart_date:
                origin = "Đà Nẵng"
                destination = "Huế"
                from datetime import datetime
                depart_date = datetime.now().strftime('%Y-%m-%d')
            
            danh_sach_chuyen = tim_kiem_chuyen_xe_kha_dung(origin, destination, depart_date)
            if not danh_sach_chuyen and search_submitted:
                messages.info(request, "Không tìm thấy chuyến xe nào phù hợp với yêu cầu.")
        else:
            danh_sach_chuyen = []

        context = {
            'chuyen_xe_list': danh_sach_chuyen,
            'origin': origin,
            'destination': destination,
            'depart_date': depart_date,
            'cac_diem_di': cac_diem_di,
            'cac_diem_den': cac_diem_den,
            'khach_hang': khach_hang,
            'sdt_mac_dinh': sdt_mac_dinh,
        }
        return render(request, 'home/timkiem.html', context)

    except Exception as e:
        messages.error(request, f"Lỗi hệ thống khi tìm kiếm: {str(e)}")
        return render(request, 'home/timkiem.html', {
            'chuyen_xe_list': [],
            'origin': origin,
            'destination': destination,
            'depart_date': depart_date,
            'cac_diem_di': cac_diem_di,
            'cac_diem_den': cac_diem_den,
            'khach_hang': khach_hang,
            'sdt_mac_dinh': sdt_mac_dinh,
        })

def lay_so_do_ghe_api(request):
    """
    API endpoint trả về sơ đồ ghế của một chuyến xe.
    """
    chuyen_id = request.GET.get('chuyen_id')
    if not chuyen_id:
        return JsonResponse({'status': 'error', 'message': 'Thiếu ID chuyến xe'}, status=400)
    
    try:
        data = lay_so_do_ghe(chuyen_id)
        return JsonResponse({'status': 'success', 'data': data})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
