from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator

# 1. Bảng Khách Hàng
class KhachHang(models.Model):
    KhachHangID = models.CharField(max_length=10, primary_key=True)
    Email = models.EmailField(max_length=100, unique=True, null=True, blank=True)
    NgayDangKy = models.DateTimeField(auto_now_add=True)
    AnhDaiDienURL = models.CharField(max_length=255, null=True, blank=True)
    def __str__(self):
        return self.KhachHangID
# 2. Bảng Nhà Xe
class Nhaxe(models.Model):
    NhaxeID = models.CharField(max_length=10, primary_key=True)
    Email = models.EmailField(max_length=100, unique=True)
    NgayDangKy = models.DateTimeField(auto_now_add=True)
    AnhDaiDien = models.ImageField(upload_to='nhaxe/', null=True, blank=True)
    DiaChiTruSo = models.TextField(max_length=200, null=True, blank=True)
    SoDienThoai = models.CharField(
        max_length=10,
        unique=True,
        validators=[RegexValidator(regex=r'^0\d{9,}$', message="Số điện thoại phải bắt đầu bằng 0 và có 10 chữ số")]
    )
    def __str__(self):
        return self.NhaxeID
# 4. Bảng Tài Xế
class Taixe(models.Model):
    TaixeID = models.CharField(max_length=10, primary_key=True)
    HoTen = models.CharField(max_length=200, null=True, blank=True)
    HinhAnhURL = models.CharField(max_length=255, null=True, blank=True)
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

    def __str__(self):
        return self.TaixeID
# 5. Bảng Chi Tiết Tài Xế (Trung gian Nhà xe - Tài xế)
class CHITIETTAIXE(models.Model):
    Nhaxe = models.ForeignKey(Nhaxe, on_delete=models.CASCADE)
    Taixe = models.ForeignKey(Taixe, on_delete=models.CASCADE)
    HoTen = models.CharField(max_length=200, null=True, blank=True)
    Tennhaxe = models.CharField(max_length=200, null=True, blank=True)
    NgayBatDau = models.DateField()
    NgayKetThuc = models.DateField()
    class Meta:
        unique_together = ('Nhaxe', 'Taixe')
# 6. Bảng Loại Xe
class Loaixe(models.Model):
    LoaixeID = models.CharField(max_length=10, primary_key=True, blank=True)
    NgayCapNhatGia = models.DateField(auto_now=True, null=True, blank=True)
    SoCho = models.IntegerField(validators=[MinValueValidator(1)])
    SoDoGheNgoiURL = models.CharField(max_length=255, null=True, blank=True)
    GiaVe = models.DecimalField(max_digits=12, decimal_places=0)

    def save(self, *args, **kwargs):
        if not self.LoaixeID:
            last_record = Loaixe.objects.order_by('LoaixeID').last()
            if last_record:
                last_id = last_record.LoaixeID
                try:
                    num = int(last_id.split('-')[1]) + 1
                    self.LoaixeID = f'LX-{num:03d}'
                except (IndexError, ValueError):
                    import uuid
                    self.LoaixeID = 'LX-' + str(uuid.uuid4())[:6]
            else:
                self.LoaixeID = 'LX-001'
        super().save(*args, **kwargs)

    def __str__(self):
        return self.LoaixeID
# 7. Bảng Chi Tiết Loại Xe (Trung gian Nhà xe - Loại xe)
class CHITIETLOAIXE(models.Model):
    Nhaxe = models.ForeignKey(Nhaxe, on_delete=models.CASCADE)
    Loaixe = models.ForeignKey(Loaixe, on_delete=models.CASCADE)
    TenLoaiXe = models.CharField(max_length=50, null=True, blank=True)
    Tennhaxe = models.CharField(max_length=200, null=True, blank=True)
    class Meta:
        unique_together = ('Nhaxe', 'Loaixe')
# 8. Bảng Xe
class Xe(models.Model):
    XeID = models.CharField(max_length=10, primary_key=True, blank=True)
    Nhaxe = models.ForeignKey(Nhaxe, on_delete=models.CASCADE)
    Loaixe = models.ForeignKey(Loaixe, on_delete=models.CASCADE)
    TrangThai = models.CharField(max_length=50, default='Đang hoạt động')
    SoGhe = models.IntegerField(null=True, blank=True)
    BienSoXe = models.CharField(max_length=20, unique=True)
    HinhAnhXe = models.ImageField(upload_to='xe/', null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.XeID:
            import re
            # Find the highest ID that follows the XE00001 pattern
            last_record = Xe.objects.filter(XeID__regex=r'^XE\d+').order_by('XeID').last()
            
            if last_record:
                match = re.search(r'(\d+)', last_record.XeID)
                num = int(match.group(1)) + 1
            else:
                num = 1
            
            # Safety loop to avoid UNIQUE constraint clusters
            new_id = f'XE{num:05d}'
            while Xe.objects.filter(XeID=new_id).exists():
                num += 1
                new_id = f'XE{num:05d}'
            
            self.XeID = new_id
            
        super().save(*args, **kwargs)

    @property
    def ten_loai_xe(self):
        """Lấy tên hãng xe từ bảng CHITIETLOAIXE"""
        try:
            from .models import CHITIETLOAIXE
            ct = CHITIETLOAIXE.objects.filter(Nhaxe=self.Nhaxe, Loaixe=self.Loaixe).first()
            return ct.TenLoaiXe if ct and ct.TenLoaiXe else self.Loaixe.LoaixeID
        except:
            return self.Loaixe.LoaixeID

    def __str__(self):
        return self.BienSoXe
# 9. Bảng Tuyến Xe
class TuyenXe(models.Model):
    tuyenXeID = models.CharField(max_length=10, primary_key=True)
    nhaXe = models.ForeignKey(Nhaxe, on_delete=models.CASCADE)
    tenTuyen = models.CharField(max_length=500, null=True, blank=True)
    diemDi = models.CharField(max_length=500, default='Đà Nẵng')
    diemDen = models.CharField(max_length=500, default='Huế')
    QuangDuong = models.CharField(max_length=100, null=True, blank=True)
    DiemTrungGian = models.CharField(max_length=500, null=True, blank=True)
    def __str__(self):
        return self.tenTuyen or self.tuyenXeID
# 10. Bảng Chuyến Xe
class ChuyenXe(models.Model):
    ChuyenXeID = models.CharField(max_length=10, primary_key=True)
    Xe = models.ForeignKey(Xe, on_delete=models.SET_NULL, null=True, blank=True)
    TuyenXe = models.ForeignKey(TuyenXe, on_delete=models.CASCADE)
    Taixe = models.ForeignKey(Taixe, on_delete=models.CASCADE)
    NgayKhoiHanh = models.DateField(null=True, blank=True)
    GioDi = models.TimeField(null=True, blank=True)
    GioDen = models.TimeField(null=True, blank=True)
    TrangThai = models.CharField(max_length=10, null=True, blank=True)
    def __str__(self):
        return self.ChuyenXeID
# 11. Bảng Ghế Ngồi
class GheNgoi(models.Model):
    gheID = models.CharField(max_length=10, primary_key=True)
    ChuyenXe = models.ForeignKey(ChuyenXe, on_delete=models.CASCADE)
    soGhe = models.CharField(max_length=5, null=True, blank=True)
    trangThai = models.CharField(max_length=20, null=True, blank=True)
    def __str__(self):
        return f"{self.soGhe} - {self.ChuyenXe.ChuyenXeID}"
# 12. Bảng Vé
class Ve(models.Model):
    VeID = models.CharField(max_length=10, primary_key=True)
    KhachHang = models.ForeignKey(KhachHang, on_delete=models.CASCADE)
    ChuyenXe = models.ForeignKey(ChuyenXe, on_delete=models.CASCADE)
    Ghe = models.ForeignKey(GheNgoi, on_delete=models.CASCADE)
    SoDienThoai = models.CharField(
        max_length=10,
        validators=[RegexValidator(regex=r'^0\d{9,}$', message="Số điện thoại phải bắt đầu bằng 0 và có 10 chữ số")]
    )
    NgayDat = models.DateTimeField(auto_now_add=True)
    GiaVe = models.DecimalField(max_digits=10, decimal_places=0)
    TrangThaiThanhToan = models.CharField(max_length=20, null=True, blank=True)
    def __str__(self):
        return self.VeID
# 13. Bảng Thanh Toán
class ThanhToan(models.Model):
    ThanhToanID = models.CharField(max_length=10, primary_key=True)
    Ve = models.OneToOneField(Ve, on_delete=models.CASCADE)
    SoTien = models.DecimalField(max_digits=19, decimal_places=4)
    PhuongThucTT = models.CharField(max_length=20, null=True, blank=True)
    NgayThanhToan = models.DateTimeField(auto_now_add=True)
    MaGiaoDich = models.CharField(max_length=50, null=True, blank=True)
    def __str__(self):
        return self.ThanhToanID
# 14. Bảng Đánh Giá
class DanhGia(models.Model):
    DanhGiaID = models.CharField(max_length=10, primary_key=True)
    Ve = models.OneToOneField(Ve, on_delete=models.CASCADE)
    KhachHang = models.ForeignKey(KhachHang, on_delete=models.CASCADE)
    Diemso = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    Nhanxet = models.TextField(max_length=500, null=True, blank=True)
    NgayDanhGia = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"Review {self.DanhGiaID} - {self.Diemso}"

# 15. Bảng User Authentication (Tự định nghĩa)
class User_Authentication(models.Model):
    UserID = models.CharField(max_length=10, primary_key=True)
    TenDangNhap = models.CharField(max_length=200, unique=True)
    MatKhau = models.CharField(max_length=200)
    Vaitro = models.CharField(max_length=20)
    SoDienThoai = models.CharField(
        max_length=12,
        unique=True,
        validators=[RegexValidator(regex=r'^0\d{9,}$', message="Số điện thoại phải bắt đầu bằng 0 và có ít nhất 10 số")]
    )
    KhachHang = models.ForeignKey(KhachHang, on_delete=models.SET_NULL, null=True, blank=True)
    Nhaxe = models.ForeignKey(Nhaxe, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.TenDangNhap

