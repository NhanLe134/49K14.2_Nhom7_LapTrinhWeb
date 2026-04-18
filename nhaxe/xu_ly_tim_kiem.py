from .models import ChuyenXe, GheNgoi, CHITIETLOAIXE
from django.db.models import Q

def tim_kiem_chuyen_xe_kha_dung(diem_di, diem_den, ngay_di):
    """
    Hàm lọc danh sách chuyến xe khả dụng dựa trên điểm đi, điểm đến và ngày khởi hành.
    Lấy đầy đủ thông tin từ các bảng liên quan: ChuyenXe, Xe (Loaixe, Nhaxe), TuyenXe, Taixe và GheNgoi.
    """
    try:
        # Lọc ChuyenXe: Khớp tuyến đường và ngày, bỏ qua các chuyến đã hoàn thành hoặc đã hủy
        # Tối ưu hóa truy vấn bằng select_related
        chuyen_xe_query = ChuyenXe.objects.filter(
            TuyenXe__diemDi__icontains=diem_di,
            TuyenXe__diemDen__icontains=diem_den,
            NgayKhoiHanh=ngay_di
        ).exclude(TrangThai__in=['Hoàn thành', 'Đã hủy'])\
         .select_related('TuyenXe', 'Xe__Loaixe', 'Xe__Nhaxe', 'Taixe')

        danh_sach_ket_qua = []
        
        for cx in chuyen_xe_query:
            # 1. Lấy thông tin chi tiết loại xe từ bảng CHITIETLOAIXE
            ct_loaixe = None
            if cx.Xe:
                ct_loaixe = CHITIETLOAIXE.objects.filter(Nhaxe=cx.Xe.Nhaxe, Loaixe=cx.Xe.Loaixe).first()
            
            ten_loai = "Xe khách"
            if ct_loaixe and ct_loaixe.TenLoaiXe:
                ten_loai = ct_loaixe.TenLoaiXe
            elif cx.Xe and cx.Xe.Loaixe:
                ten_loai = f"Xe {cx.Xe.Loaixe.SoCho} chỗ"

            # 2. Tính toán số chỗ trống dựa trên bảng GheNgoi và quy tắc trừ ghế tài xế
            # Quy tắc: 4->3, 7->7 (B1-B7), 9->8
            tong_ghe_xe = cx.Xe.Loaixe.SoCho if cx.Xe and cx.Xe.Loaixe else 4
            if tong_ghe_xe == 4: tong_ghe_ban = 3
            elif tong_ghe_xe == 7: tong_ghe_ban = 7
            elif tong_ghe_xe == 9: tong_ghe_ban = 8
            else: tong_ghe_ban = max(0, tong_ghe_xe - 1)

            ghe_ngoi_qs = GheNgoi.objects.filter(ChuyenXe=cx)
            tong_so_ghe_hien_tai = ghe_ngoi_qs.count()
            
            if tong_so_ghe_hien_tai == 0:
                so_cho_trong = tong_ghe_ban
            else:
                # Chỉ tính những ghế có mã khớp với quy chuẩn (A, B, C) và chưa đặt
                so_cho_trong = ghe_ngoi_qs.exclude(trangThai='Đã đặt').count()
                # Đảm bảo không vượt quá số ghế bán được
                so_cho_trong = min(so_cho_trong, tong_ghe_ban)

            # 3. Tổng hợp dữ liệu trả về cho template
            item = {
                'ChuyenXeID': cx.ChuyenXeID,
                'GioDi': cx.GioDi,
                'GioDen': cx.GioDen,
                'NgayKhoiHanh': cx.NgayKhoiHanh,
                'tenTuyen': cx.TuyenXe.tenTuyen if cx.TuyenXe else 'N/A',
                'DiemDi': cx.TuyenXe.diemDi if cx.TuyenXe else '',
                'DiemDen': cx.TuyenXe.diemDen if cx.TuyenXe else '',
                'GiaVe': cx.Xe.Loaixe.GiaVe if cx.Xe and cx.Xe.Loaixe else 0,
                'TenNhaXe': cx.Xe.Nhaxe.TenNhaXe if cx.Xe and cx.Xe.Nhaxe else 'N/A',
                'LoaiXe': ten_loai,
                'BienSoXe': cx.Xe.BienSoXe if cx.Xe else '',
                'TenTaiXe': cx.Taixe.HoTen if cx.Taixe else 'Chưa rõ',
                'SoChoTrong': so_cho_trong,
                'TongSoCho': tong_ghe_ban,
                'TrangThai': cx.TrangThai or 'Đang chờ'
            }
            danh_sach_ket_qua.append(item)

        return danh_sach_ket_qua

    except Exception as e:
        print(f"Lỗi truy vấn ChuyenXe: {str(e)}")
        raise e

def lay_so_do_ghe(chuyen_xe_id):
    """
    Hàm lấy sơ đồ ghế và trạng thái thực tế của từng ghế trong chuyến xe.
    Quy tắc:
    - Xe 4 chỗ: A1 -> A3
    - Xe 7 chỗ: B1 -> B6
    - Xe 9 chỗ: C1 -> C8
    """
    try:
        chuyen = ChuyenXe.objects.select_related('Xe__Loaixe').get(ChuyenXeID=chuyen_xe_id)
        # Lấy số chỗ từ Loại xe
        tong_cho = chuyen.Xe.Loaixe.SoCho if chuyen.Xe and chuyen.Xe.Loaixe else 4
        
        prefix = "A"
        count = 3
        if tong_cho == 4:
            prefix, count = "A", 3
        elif tong_cho == 7:
            prefix, count = "B", 7
        elif tong_cho == 9:
            prefix, count = "C", 8
        else:
            prefix, count = "S", tong_cho - 1

        # Tạo danh sách nhãn ghế
        labels = [f"{prefix}{i}" for i in range(1, count + 1)]

        # Truy vấn các ghế đã có trong DB (để biết trạng thái Đã đặt)
        ghe_db = GheNgoi.objects.filter(ChuyenXe=chuyen)
        # Tạo map với key đã chuẩn hóa (strip và viết hoa)
        ghe_status_map = {str(g.soGhe).strip().upper(): g.trangThai for g in ghe_db if g.soGhe}

        danh_sach_ghe = []
        for label in labels:
            # Lấy trạng thái từ map theo label đã chuẩn hóa
            db_status = ghe_status_map.get(label.upper(), "Còn trống")
            
            # Chuẩn hóa trạng thái để so sánh
            str_status = str(db_status).strip().lower()
            
            # Nếu status chứa cụm "đã đặt" -> sold (màu xanh blue #1da1f2)
            # Ngược lại là available (màu xám gray #999)
            if "đã đặt" in str_status:
                final_status = "sold"
            else:
                final_status = "available"

            danh_sach_ghe.append({
                "soGhe": label,
                "trangThai": final_status
            })
            
        return danh_sach_ghe

    except ChuyenXe.DoesNotExist:
        return []
    except Exception as e:
        print(f"Lỗi lấy sơ đồ ghế: {str(e)}")
        raise e
