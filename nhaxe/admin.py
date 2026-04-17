from django.contrib import admin
from .models import (
    KhachHang, Nhaxe, Taixe, CHITIETTAIXE,
    Loaixe, CHITIETLOAIXE, Xe, TuyenXe, ChuyenXe, GheNgoi, Ve,
    ThanhToan, DanhGia
)

# Customize admin site headers
admin.site.site_header = 'Hệ Thống Quản Lý Đặt Vé Xe'
admin.site.index_title = 'Quản Trị Hệ Thống'
admin.site.site_title = 'Admin Control Panel'

# Đăng ký từng model kèm hiển thị cột (tuỳ chọn)
@admin.register(KhachHang)
class KhachHangAdmin(admin.ModelAdmin):
    list_display = ('KhachHangID', 'Email', 'NgayDangKy')
    search_fields = ('KhachHangID', 'Email')

@admin.register(Nhaxe)
class NhaxeAdmin(admin.ModelAdmin):
    list_display = ('NhaxeID', 'Email', 'SoDienThoai', 'NgayDangKy')
    search_fields = ('NhaxeID', 'Email', 'SoDienThoai')


@admin.register(Taixe)
class TaixeAdmin(admin.ModelAdmin):
    list_display = ('TaixeID', 'HoTen', 'SoBangLai', 'soCCCD', 'LoaiBangLai')
    search_fields = ('TaixeID', 'HoTen', 'SoBangLai', 'soCCCD')

@admin.register(CHITIETTAIXE)
class ChiTietTaiXeAdmin(admin.ModelAdmin):
    list_display = ('Nhaxe', 'Taixe', 'HoTen', 'NgayBatDau', 'NgayKetThuc')

@admin.register(Loaixe)
class LoaixeAdmin(admin.ModelAdmin):
    list_display = ('LoaixeID', 'SoCho', 'GiaVe', 'NgayCapNhatGia')

@admin.register(CHITIETLOAIXE)
class ChiTietLoaiXeAdmin(admin.ModelAdmin):
    list_display = ('Nhaxe', 'Loaixe', 'TenLoaiXe')

@admin.register(Xe)
class XeAdmin(admin.ModelAdmin):
    list_display = ('XeID', 'BienSoXe', 'Nhaxe', 'Loaixe', 'TrangThai')
    search_fields = ('XeID', 'BienSoXe')

@admin.register(TuyenXe)
class TuyenXeAdmin(admin.ModelAdmin):
    list_display = ('tuyenXeID', 'tenTuyen', 'nhaXe', 'diemDi', 'diemDen')

@admin.register(ChuyenXe)
class ChuyenXeAdmin(admin.ModelAdmin):
    list_display = ('ChuyenXeID', 'TuyenXe', 'Xe', 'NgayKhoiHanh', 'GioDi', 'TrangThai')
    list_filter = ('TrangThai', 'NgayKhoiHanh')

@admin.register(GheNgoi)
class GheNgoiAdmin(admin.ModelAdmin):
    list_display = ('gheID', 'ChuyenXe', 'soGhe', 'trangThai')
    list_filter = ('trangThai',)

@admin.register(Ve)
class VeAdmin(admin.ModelAdmin):
    list_display = ('VeID', 'KhachHang', 'ChuyenXe', 'Ghe', 'GiaVe', 'NgayDat', 'TrangThaiThanhToan')
    list_filter = ('TrangThaiThanhToan', 'NgayDat')

@admin.register(ThanhToan)
class ThanhToanAdmin(admin.ModelAdmin):
    list_display = ('ThanhToanID', 'Ve', 'SoTien', 'PhuongThucTT', 'NgayThanhToan')

@admin.register(DanhGia)
class DanhGiaAdmin(admin.ModelAdmin):
    list_display = ('DanhGiaID', 'Ve', 'KhachHang', 'Diemso', 'NgayDanhGia')
    list_filter = ('Diemso',)
