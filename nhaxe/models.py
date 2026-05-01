from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
import re

# 1. Bảng KhachHang (Khách hàng)
class KhachHang(models.Model):
    KhachHangID = models.CharField(max_length=10, primary_key=True)
    HovaTen = models.CharField(max_length=200, null=True, blank=True) # Sửa từ HoVaTen
    Email = models.CharField(max_length=100, unique=True, null=True, blank=True)
    NgaySinh = models.DateField(null=True, blank=True)
    NgayDangKy = models.DateTimeField(auto_now_add=True, null=True, blank=True) # Thêm trường này
    AnhDaiDienURL = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.HovaTen or self.KhachHangID

# 3. Bảng Nhaxe (Nhà xe)
class Nhaxe(models.Model):
    NhaxeID = models.CharField(max_length=10, primary_key=True)
    Email = models.CharField(max_length=100, unique=True)
    NgayDangKy = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    AnhDaiDienURL = models.TextField(null=True,blank=True)
    DiaChiTruSo = models.CharField(max_length=200, null=True, blank=True)
    TenNhaXe = models.CharField(max_length=200, null=True, blank=True) # Tên nhà xe
    NguoiDaiDien = models.CharField(max_length=200, null=True, blank=True) # Tên người đại diện (từ DB cũ)
    HoTenNguoiDaiDien = models.CharField(max_length=200, null=True, blank=True) # Họ tên người đại diện
    SoDienThoai = models.CharField(
        max_length=20,  # Nới rộng từ 10 thành 20
        unique=True,
        validators=[RegexValidator(regex=r'^\d{10,12}$', message="SĐT nhà xe phải có từ 10-12 chữ số")]
    )
    SoLuotDanhGia = models.IntegerField(default=0)
    TongDiemDanhGia = models.IntegerField(default=0)
    
    # Thông tin thanh toán (VietQR)
    MaNganHang = models.CharField(max_length=50, null=True, blank=True, help_text="Ví dụ: MB, VCB, ICB")
    SoTaiKhoan = models.CharField(max_length=50, null=True, blank=True)
    TenChuTaiKhoan = models.CharField(max_length=200, null=True, blank=True)
    
    # TRƯỜNG THÊM MỚI: % Hoa hồng
    PhanTramHoaHong = models.DecimalField(max_digits=5, decimal_places=2, default=10.0)

    def __str__(self):
        return self.NhaxeID

# 2. Bảng User_Authentication (Xác thực người dùng)
class User_Authentication(models.Model):
    UserID = models.CharField(max_length=10, primary_key=True)
    KhachHang = models.ForeignKey(KhachHang, on_delete=models.SET_NULL, null=True, blank=True)
    Nhaxe = models.ForeignKey(Nhaxe, on_delete=models.SET_NULL, null=True, blank=True)
    Taixe = models.ForeignKey('Taixe', on_delete=models.SET_NULL, null=True, blank=True)
    TenDangNhap = models.CharField(max_length=200, unique=True)
    MatKhau = models.CharField(max_length=200)
    Vaitro = models.CharField(max_length=20) # 'Nhaxe' hoặc 'Khach'
    SoDienThoai = models.CharField(
        max_length=20, 
        unique=True,
        null=True, blank=True,
        validators=[RegexValidator(regex=r'^\d{10,12}$', message="SĐT phải từ 10-12 số")]
    )

    def __str__(self):
        return self.TenDangNhap

# 4. Bảng Taixe (Tài xế)
class Taixe(models.Model):
    TaixeID = models.CharField(max_length=10, primary_key=True)
    HoTen = models.CharField(max_length=200, null=True, blank=True)
    HinhAnhURL = models.TextField(null=True,blank=True)
    SoBangLai = models.CharField(max_length=20, unique=True)
    soCCCD = models.CharField(
        max_length=12, 
        unique=True,
        validators=[RegexValidator(regex=r'^\d{12}$', message="CCCD phải có đúng 12 chữ số")]
    )
    LOAI_BANG_CHOICES = [
        ('B1', 'B1'),
        ('B', 'B'),
        ('C', 'C'),
        ('C1', 'C1'),
    ]
    LoaiBangLai = models.CharField(
        max_length=2, 
        choices=LOAI_BANG_CHOICES, 
        default='B1',
        null=True, 
        blank=True
    )
    NgayHetHanBangLai = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.TaixeID

# 5. Bảng CHITIETTAIXE (Chi tiết tài xế - Liên kết nhà xe)
class CHITIETTAIXE(models.Model):
    Nhaxe = models.ForeignKey(Nhaxe, on_delete=models.CASCADE, db_column='Nhaxe_id')
    Taixe = models.ForeignKey(Taixe, on_delete=models.CASCADE)
    HoTen = models.CharField(max_length=200, null=True, blank=True)
    NgayBatDau = models.DateField()
    NgayKetThuc = models.DateField()

    class Meta:
        unique_together = (('Nhaxe', 'Taixe'),)

# 6. Bảng Loaixe (Loại xe)
class Loaixe(models.Model):
    LoaixeID = models.CharField(max_length=10, primary_key=True)
    # TenLoaiXe = models.CharField(max_length=50, null=True, blank=True)
    SoCho = models.IntegerField(validators=[MinValueValidator(1)])
    SoDoGheNgoiURL = models.CharField(max_length=255, null=True, blank=True)
    GiaVe = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    NgayCapNhatGia = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.LoaixeID

# 7. Bảng CHITIETLOAIXE (Chi tiết loại xe - Liên kết nhà xe)
class CHITIETLOAIXE(models.Model):
    Nhaxe = models.ForeignKey(Nhaxe, on_delete=models.CASCADE)
    Loaixe = models.ForeignKey(Loaixe, on_delete=models.CASCADE)
    TenLoaiXe = models.CharField(max_length=50, null=True, blank=True) # Tên tùy chỉnh của nhà xe cho loại xe này
    GiaVe = models.DecimalField(max_digits=12, decimal_places=0, default=0) # Giá riêng của nhà xe cho loại xe này
    NgayCapNhatGia = models.DateField(null=True, blank=True) # Ngày cập nhật giá riêng
    # Tennhaxe có vẻ không cần thiết nếu đã có Nhaxe FK

    class Meta:
        unique_together = (('Nhaxe', 'Loaixe'),)

# 8. Bảng Xe
class Xe(models.Model):
    XeID = models.CharField(max_length=10, primary_key=True)
    Nhaxe = models.ForeignKey(Nhaxe, on_delete=models.CASCADE)
    Loaixe = models.ForeignKey(Loaixe, on_delete=models.CASCADE)
    TrangThai = models.CharField(max_length=50, null=True, blank=True) # Nới rộng thành 50
    SoGhe = models.IntegerField(null=True, blank=True)
    BienSoXe = models.CharField(max_length=20, unique=True)
    HinhAnhXe = models.ImageField(upload_to='xe_images/', null=True, blank=True)

    @property
    def ten_loai_xe(self):
        chi_tiet = CHITIETLOAIXE.objects.filter(Nhaxe=self.Nhaxe, Loaixe=self.Loaixe).first()
        if chi_tiet and chi_tiet.TenLoaiXe:
            return chi_tiet.TenLoaiXe

        so_cho = self.Loaixe.SoCho if self.Loaixe else 0
        if so_cho == 4: return "Loại xe A"
        if so_cho == 7: return "Loại xe B"
        if so_cho == 9: return "Loại xe C"
        return f"Loại xe {so_cho} chỗ"

    def __str__(self):
        return self.BienSoXe

# 9. Bảng TuyenXe (Tuyến xe)
class TuyenXe(models.Model):
    tuyenXeID = models.CharField(max_length=10, primary_key=True)
    nhaXe = models.ForeignKey(Nhaxe, on_delete=models.CASCADE)
    tenTuyen = models.CharField(max_length=500, null=True, blank=True)
    diemDi = models.CharField(max_length=500, default='Đà Nẵng')
    diemDen = models.CharField(max_length=500, default='Huế')
    QuangDuong = models.IntegerField(null=True, blank=True)
    DiemTrungGian = models.CharField(max_length=500, null=True, blank=True)
    ThoiGian = models.FloatField(null=True, blank=True) # Thời gian di chuyển (giờ)

    def __str__(self):
        return self.tenTuyen if self.tenTuyen else self.tuyenXeID

# 10. Bảng ChuyenXe (Chuyến xe)
class ChuyenXe(models.Model):
    ChuyenXeID = models.CharField(max_length=10, primary_key=True)
    Xe = models.ForeignKey(Xe, on_delete=models.SET_NULL, null=True, blank=True)
    TuyenXe = models.ForeignKey(TuyenXe, on_delete=models.CASCADE)
    Taixe = models.ForeignKey(Taixe, on_delete=models.CASCADE,null=True,blank=True)
    NgayKhoiHanh = models.DateField(null=True, blank=True)
    GioDi = models.TimeField(null=True, blank=True)
    GioDen = models.TimeField(null=True, blank=True)
    TrangThai = models.CharField(max_length=50, null=True, blank=True, default='Chưa hoàn thành')

    def save(self, *args, **kwargs):
        # Tự động tính GioDen = GioDi + TuyenXe.ThoiGian
        if self.GioDi:
            try:
                import datetime
                gio_di_obj = self.GioDi
                if isinstance(gio_di_obj, str):
                    if len(gio_di_obj) == 5:
                        gio_di_obj = datetime.datetime.strptime(gio_di_obj, '%H:%M').time()
                    else:
                        gio_di_obj = datetime.datetime.strptime(gio_di_obj, '%H:%M:%S').time()

                tuyen = self.TuyenXe
                if isinstance(gio_di_obj, datetime.time) and tuyen and tuyen.ThoiGian:
                    full_datetime = datetime.datetime.combine(datetime.date.today(), gio_di_obj)
                    arrival_datetime = full_datetime + datetime.timedelta(hours=float(tuyen.ThoiGian))
                    self.GioDen = arrival_datetime.time()
            except Exception as e:
                print(f"Lỗi tính giờ đến: {e}")

        is_new = not self.ChuyenXeID
        if is_new:
            # Tìm mã CX00001, CX00002... còn trống đầu tiên
            num = 1
            while True:
                new_id = f'CX{num:05d}'
                if not ChuyenXe.objects.filter(ChuyenXeID=new_id).exists():
                    self.ChuyenXeID = new_id
                    break
                num += 1

        super().save(*args, **kwargs)

        # Tự động tạo ghế nếu là chuyến xe mới
        if is_new and self.Xe and self.Xe.Loaixe:
            so_cho = self.Xe.Loaixe.SoCho
            prefix = 'A'
            if so_cho == 7: prefix = 'B'
            elif so_cho == 9: prefix = 'C'

            ghe_list = []
            for i in range(1, so_cho + 1):
                so_ghe_str = f"{prefix}{i}"
                ghe_id = f"{self.ChuyenXeID}{so_ghe_str}"
                # Tránh tạo trùng nếu đã tồn tại
                if not GheNgoi.objects.filter(gheID=ghe_id).exists():
                    ghe_list.append(GheNgoi(
                        gheID=ghe_id,
                        ChuyenXe=self,
                        soGhe=so_ghe_str,
                        trangThai='Còn trống'
                    ))

            if ghe_list:
                GheNgoi.objects.bulk_create(ghe_list)


    def __str__(self):
        return self.ChuyenXeID

# 11. Bảng Ghế Ngồi
class GheNgoi(models.Model):
    gheID = models.CharField(max_length=20, primary_key=True, db_column='gheid') # Nới rộng để chứa CX00001A1
    ChuyenXe = models.ForeignKey(ChuyenXe, on_delete=models.CASCADE, db_column='chuyenxe_id')
    soGhe = models.CharField(max_length=10, null=True, blank=True, db_column='soghe')
    trangThai = models.CharField(max_length=20, default='Còn trống', db_column='trangthai')

    def __str__(self):
        return f"{self.soGhe} - {self.ChuyenXe.ChuyenXeID}"

# 12. Bảng Vé
class Ve(models.Model):
    VeID = models.CharField(max_length=10, primary_key=True)
    KhachHang = models.ForeignKey(KhachHang, on_delete=models.CASCADE, db_column='KhachHang_id')
    ChuyenXe = models.ForeignKey(ChuyenXe, on_delete=models.CASCADE, db_column='ChuyenXe_id')
    Ghe = models.ForeignKey(GheNgoi, on_delete=models.CASCADE, db_column='Ghe_id')
    SoDienThoai = models.CharField(
        max_length=20,
        validators=[RegexValidator(regex=r'^\d{10,12}$', message="SĐT phải có từ 10-12 số")]
    )
    HoTen = models.CharField(max_length=200, null=True, blank=True, db_column='Hoten')
    DiemDon = models.CharField(max_length=500, null=True, blank=True, db_column='DiemDon')
    DiemTra = models.CharField(max_length=500, null=True, blank=True, db_column='DiemTra')
    NgayDat = models.DateTimeField(auto_now_add=True)
    GiaVe = models.DecimalField(max_digits=12, decimal_places=0)
    TrangThai = models.CharField(max_length=50, default='Đã đặt')
    TrangThaiThanhToan = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return self.VeID

# 13. Bảng Thanh Toán
class ThanhToan(models.Model):
    ThanhToanID = models.CharField(max_length=10, primary_key=True)
    Ve = models.OneToOneField(Ve, on_delete=models.CASCADE)
    SoTien = models.DecimalField(max_digits=12, decimal_places=0)
    NgayThanhToan = models.DateTimeField(null=True, blank=True)
    DaQuyetToan = models.BooleanField(default=False, verbose_name="Đã quyết toán")

    def __str__(self):
        return self.ThanhToanID

# 14. Bảng Đánh Giá (Đánh giá)
class DanhGia(models.Model):
    DanhGiaID = models.CharField(max_length=10, primary_key=True)
    Nhaxe = models.ForeignKey(Nhaxe, on_delete=models.CASCADE)
    KhachHang = models.ForeignKey(KhachHang, on_delete=models.CASCADE)
    Ve = models.ForeignKey('Ve', on_delete=models.CASCADE, null=True, blank=True)
    Diemso = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    Nhanxet = models.CharField(max_length=500, null=True, blank=True)
    NgayDanhGia = models.DateTimeField(null=True, blank=True)
    AnDanh = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.DanhGiaID} - {self.Diemso} sao"

# 15. Bảng NganHangAdmin (Cấu hình ngân hàng hệ thống)
class NganHangAdmin(models.Model):
    TenChuTaiKhoan = models.CharField(max_length=200)
    MaNganHang = models.CharField(max_length=50)
    SoTaiKhoan = models.CharField(max_length=50)

    class Meta:
        verbose_name = "Cấu hình Ngân hàng Admin"
        verbose_name_plural = "Cấu hình Ngân hàng Admin"

    def __str__(self):
        return f"{self.TenChuTaiKhoan} - {self.MaNganHang}"
