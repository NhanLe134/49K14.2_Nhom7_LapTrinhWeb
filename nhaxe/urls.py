from django.urls import path
from . import views
from . import auth_views
from . import chuyenxe_views

urlpatterns = [

    # ==================== TRANG CHUNG ====================
    path('', auth_views.index, name='index'),
    path('dangnhap', auth_views.dangnhap, name='dangnhap'),
    path('dangxuat', auth_views.dangxuat, name='dangxuat'),
    path('timkiem', views.timkiem, name='timkiem'),
    path('quen_mat_khau', views.quen_mat_khau, name='quen_mat_khau'),
    path('dangky_khachhang', views.dangky_khachhang, name='dangky_khachhang'),
    path('dangky_nhaxe', views.dangky_nhaxe, name='dangky_nhaxe'),

    # ==================== KHÁCH HÀNG ====================
    path('khachhang', views.khachhang, name='khachhang'),
    path('thongtin_khachhang', views.thongtin_khachhang, name='thongtin_khachhang'),
    path('lotrinh', views.lotrinh, name='lotrinh'),
    path('chitietchuyenxe', views.chitietchuyenxe, name='chitietchuyenxe'),
    path('vecuatoi', views.vecuatoi, name='vecuatoi'),
    path('vietdanhgia', views.vietdanhgia, name='vietdanhgia'),
    path('dadanhgia', views.dadanhgia, name='dadanhgia'),
    path('danhgiachuyenxe', views.danhgiachuyenxe, name='danhgiachuyenxe'),

    # ==================== NHÀ XE ====================
    path('nhaxe', views.nhaxe, name='nhaxe'),
    path('thong_tin_nha_xe', views.thong_tin_nha_xe, name='thong_tin_nha_xe'),
    path('quanlychuyenxe', chuyenxe_views.quanlychuyenxe, name='quanlychuyenxe'),
    path('themchuyenxe', chuyenxe_views.themchuyenxe, name='themchuyenxe'),
    path('suachuyenxe', chuyenxe_views.suachuyenxe, name='suachuyenxe'),
    path('quanlytuyenxe', views.quanlytuyenxe, name='quanlytuyenxe'),
    path('quanly_loaixe', views.quanly_loaixe, name='quanly_loaixe'),
    path('quan_ly_xe', views.quan_ly_xe, name='quan_ly_xe'),
    path('quanlytaixe', views.quanlytaixe, name='quanlytaixe'),
    path('quanly_khachhang', views.quanly_khachhang, name='quanly_khachhang'),
    path('quanlyve', views.quanlyve, name='quanlyve'),

    # ==================== TÀI XẾ ====================
    path('taixe', views.taixe, name='taixe'),
    path('thongtin_taixe', views.thongtin_taixe, name='thongtin_taixe'),
    path('taixe_quanlychuyenxe', chuyenxe_views.taixe_quanlychuyenxe, name='taixe_quanlychuyenxe'),
    path('taixe_chitietchuyenxe', chuyenxe_views.taixe_chitietchuyenxe, name='taixe_chitietchuyenxe'),
    path('taixe_lotrinh', views.taixe_lotrinh, name='taixe_lotrinh'),
    path('phancongtaixe', views.phancongtaixe, name='phancongtaixe'),
]