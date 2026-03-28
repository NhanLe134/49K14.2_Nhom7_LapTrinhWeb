from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


# 3.1 Bảng Nhà xe
class NhaXe(models.Model):
    NhaxeID = models.CharField(max_length=10, primary_key=True)
    Hoten = models.CharField(max_length=200)
    Email = models.CharField(max_length=100)
    NgayDangKy = models.DateTimeField(null=True, blank=True)
    AnhDaiDienURL = models.CharField(max_length=100, null=True, blank=True)
    DiaChiTruSo = models.CharField(max_length=200, null=True, blank=True)
    SoDienThoai = models.CharField(max_length=12, unique=True)

    class Meta:
        db_table = 'NhaXe'

    def __str__(self):
        return self.Hoten


# 3.2 Bảng Tài xế
class TaiXe(models.Model):
    TaixeID = models.CharField(max_length=10, primary_key=True)
    NhaxeID = models.ForeignKey(
        NhaXe, on_delete=models.CASCADE,
        db_column='NhaxeID'
    )
    HoTen = models.CharField(max_length=200)
    SoCCCD = models.CharField(max_length=12, null=True, blank=True)
    LoaiBangLai = models.CharField(max_length=20, null=True, blank=True)
    NgayHetHanBangLai = models.DateTimeField(null=True, blank=True)
    HinhAnhURL = models.CharField(max_length=100, null=True, blank=True)
    SoBangLai = models.CharField(max_length=20, null=True, blank=True)

    class Meta:
        db_table = 'TaiXe'

    def __str__(self):
        return self.HoTen


# 3.3 Bảng Tuyến xe
class TuyenXe(models.Model):
    TuyenXeID = models.CharField(max_length=10, primary_key=True)
    NhaxeID = models.ForeignKey(
        NhaXe, on_delete=models.CASCADE,
        db_column='NhaxeID'
    )
    TenTuyen = models.CharField(max_length=500)
    DiemDi = models.CharField(max_length=500)
    DiemDen = models.CharField(max_length=500)
    QuangDuong = models.CharField(max_length=500, null=True, blank=True)
    DiemTrungGian = models.CharField(max_length=500, null=True, blank=True)

    class Meta:
        db_table = 'TuyenXe'

    def __str__(self):
        return self.TenTuyen


# 3.4 Bảng Loại xe
class LoaiXe(models.Model):
    LoaiXeID = models.CharField(max_length=10, primary_key=True)
    NhaxeID = models.ForeignKey(
        NhaXe, on_delete=models.SET_NULL,
        null=True, blank=True,
        db_column='NhaxeID'
    )
    TenLoaiXe = models.CharField(max_length=50)
    SoCho = models.IntegerField(validators=[MinValueValidator(1)])
    SoDoGheNgoiURL = models.CharField(max_length=100, null=True, blank=True)
    GiaVe = models.DecimalField(
        max_digits=15, decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(0)]
    )
    NgayCapNhatGia = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'LoaiXe'

    def __str__(self):
        return self.TenLoaiXe


# 3.5 Bảng Xe
class Xe(models.Model):
    XeID = models.CharField(max_length=10, primary_key=True)
    NhaxeID = models.ForeignKey(
        NhaXe, on_delete=models.SET_NULL,
        null=True, blank=True,
        db_column='NhaxeID'
    )
    BienSoXe = models.CharField(max_length=20, unique=True, null=True, blank=True)
    TrangThai = models.CharField(max_length=20, null=True, blank=True)
    SoGhe = models.CharField(max_length=10, null=True, blank=True)

    class Meta:
        db_table = 'Xe'

    def __str__(self):
        return self.XeID


# 3.6 Bảng Chuyến xe
class ChuyenXe(models.Model):
    ChuyenXeID = models.CharField(max_length=10, primary_key=True)
    XeID = models.ForeignKey(
        Xe, on_delete=models.SET_NULL,
        null=True, blank=True,
        db_column='XeID'
    )
    TuyenXeID = models.ForeignKey(
        TuyenXe, on_delete=models.SET_NULL,
        null=True, blank=True,
        db_column='TuyenXeID'
    )
    TaixeID = models.ForeignKey(
        TaiXe, on_delete=models.SET_NULL,
        null=True, blank=True,
        db_column='TaixeID'
    )
    NgayKhoiHanh = models.DateTimeField()
    GioDi = models.DateTimeField(null=True, blank=True)
    GioDen = models.DateTimeField(null=True, blank=True)
    TrangThai = models.CharField(max_length=10, null=True, blank=True)

    class Meta:
        db_table = 'ChuyenXe'

    def __str__(self):
        return self.ChuyenXeID


# 3.7 Bảng Ghế ngồi
class GheNgoi(models.Model):
    GheID = models.CharField(max_length=10, primary_key=True)
    XeID = models.ForeignKey(
        Xe, on_delete=models.SET_NULL,
        null=True, blank=True,
        db_column='XeID'
    )
    ChuyenXeID = models.ForeignKey(
        ChuyenXe, on_delete=models.SET_NULL,
        null=True, blank=True,
        db_column='ChuyenXeID'
    )
    SoGhe = models.CharField(max_length=5)
    TrangThai = models.CharField(max_length=20, null=True, blank=True)

    class Meta:
        db_table = 'GheNgoi'

    def __str__(self):
        return self.GheID


# 3.8 Bảng Khách hàng
class KhachHang(models.Model):
    KhachHangID = models.CharField(max_length=10, primary_key=True)
    HoTen = models.CharField(max_length=200)
    Email = models.CharField(max_length=100, null=True, blank=True)
    NgayDangKy = models.DateTimeField(null=True, blank=True)
    AnhDaiDienURL = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        db_table = 'KhachHang'

    def __str__(self):
        return self.HoTen


# 3.9 Bảng Vé
class Ve(models.Model):
    VeID = models.CharField(max_length=10, primary_key=True)
    KhachHangID = models.ForeignKey(
        KhachHang, on_delete=models.SET_NULL,
        null=True, blank=True,
        db_column='KhachHangID'
    )
    ChuyenXeID = models.ForeignKey(
        ChuyenXe, on_delete=models.SET_NULL,
        null=True, blank=True,
        db_column='ChuyenXeID'
    )
    GheID = models.ForeignKey(
        GheNgoi, on_delete=models.SET_NULL,
        null=True, blank=True,
        db_column='GheID'
    )
    TenHanhKhach = models.CharField(max_length=200)
    SoDienThoai = models.CharField(max_length=10, null=True, blank=True)
    NgayDat = models.DateTimeField(null=True, blank=True)
    GiaVe = models.DecimalField(
        max_digits=15, decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(0)]
    )
    TrangThaiThanhToan = models.CharField(max_length=20, null=True, blank=True)
    DiemDon = models.CharField(max_length=150, null=True, blank=True)
    DiemTra = models.CharField(max_length=150, null=True, blank=True)

    class Meta:
        db_table = 'Ve'

    def __str__(self):
        return self.VeID


# 3.10 Bảng Thanh toán
class ThanhToan(models.Model):
    ThanhToanID = models.CharField(max_length=10, primary_key=True)
    VeID = models.ForeignKey(
        Ve, on_delete=models.SET_NULL,
        null=True, blank=True,
        db_column='VeID'
    )
    SoTien = models.DecimalField(
        max_digits=15, decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(0)]
    )
    PhuongThucTT = models.CharField(max_length=20, null=True, blank=True)
    TrangThaiThanhToan = models.CharField(max_length=20, null=True, blank=True)
    NgayThanhToan = models.DateTimeField(null=True, blank=True)
    MaGiaoDich = models.CharField(max_length=10, null=True, blank=True)

    class Meta:
        db_table = 'ThanhToan'

    def __str__(self):
        return self.ThanhToanID


# 3.11 Bảng Đánh giá
class DanhGia(models.Model):
    DanhGiaID = models.CharField(max_length=10, primary_key=True)
    VeID = models.ForeignKey(
        Ve, on_delete=models.SET_NULL,
        null=True, blank=True,
        db_column='VeID'
    )
    KhachHangID = models.ForeignKey(
        KhachHang, on_delete=models.SET_NULL,
        null=True, blank=True,
        db_column='KhachHangID'
    )
    DiemSo = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    NhanXet = models.CharField(max_length=500, null=True, blank=True)
    NgayDanhGia = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'DanhGia'

    def __str__(self):
        return self.DanhGiaID