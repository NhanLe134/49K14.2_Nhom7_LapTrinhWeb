from django.urls import path
from . import views
from . import auth_views
from . import chuyenxe_views
from . import taixe_views
from . import tuyenxe_views
from . import feedback_views

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
    path('vietdanhgia/<str:ve_id>/', feedback_views.vietdanhgia, name='vietdanhgia'),
    path('danhgiachuyenxe', feedback_views.danhgiachuyenxe, name='danhgiachuyenxe'),
    path('submit_danhgia', feedback_views.submit_danhgia, name='submit_danhgia'),

    # ==================== NHÀ XE ====================
    path('nhaxe', views.nhaxe, name='nhaxe'),
    path('thong_tin_nha_xe', views.thong_tin_nha_xe, name='thong_tin_nha_xe'),
    path('quanlychuyenxe', chuyenxe_views.quanlychuyenxe, name='quanlychuyenxe'),
    path('themchuyenxe', chuyenxe_views.themchuyenxe, name='themchuyenxe'),
    path('suachuyenxe', chuyenxe_views.suachuyenxe, name='suachuyenxe'),
    path('hoanthanh-chuyenxe/<str:pk>/', chuyenxe_views.hoanthanh_chuyenxe, name='hoanthanh_chuyenxe'),
    path('quanlytuyenxe', tuyenxe_views.quanlytuyenxe, name='quanlytuyenxe'),
    path('them-tuyen-xe', tuyenxe_views.them_tuyen_xe, name='them_tuyen_xe'),
    path('sua-tuyen-xe/<str:pk>/', tuyenxe_views.sua_tuyen_xe, name='sua_tuyen_xe'),
    path('xoa-tuyen-xe/<str:pk>/', tuyenxe_views.xoa_tuyen_xe, name='xoa_tuyen_xe'),
    path('quan_ly_xe', views.quan_ly_xe, name='quan_ly_xe'),
    path('quanlytaixe', taixe_views.quanlytaixe, name='quanlytaixe'),
    path('them-tai-xe', taixe_views.them_tai_xe, name='them_tai_xe'),
    path('sua-tai-xe/<str:pk>/', taixe_views.sua_tai_xe, name='sua_tai_xe'),
    path('xoa-tai-xe/<str:pk>/', taixe_views.xoa_tai_xe, name='xoa_tai_xe'),
    path('quanly_khachhang', views.quanly_khachhang, name='quanly_khachhang'),
    path('quanlyve', views.quanlyve, name='quanlyve'),
    path('quanly_loaixe', views.quanly_loaixe, name='quanly_loaixe'),
    path('cap-nhat-gia/<str:loaixe_id>/', views.capnhat_gia_loaixe, name='capnhat_gia_loaixe'),

    # ==================== TÀI XẾ ====================
    path('taixe', taixe_views.taixe, name='taixe'),
    path('thongtin_taixe', taixe_views.thongtin_taixe, name='thongtin_taixe'),
    path('taixe_quanlychuyenxe', chuyenxe_views.taixe_quanlychuyenxe, name='taixe_quanlychuyenxe'),
    path('taixe_chitietchuyenxe', chuyenxe_views.taixe_chitietchuyenxe, name='taixe_chitietchuyenxe'),
    path('taixe_lotrinh', taixe_views.taixe_lotrinh, name='taixe_lotrinh'),
    path('phancongtaixe', taixe_views.phancongtaixe, name='phancongtaixe'),
# Thao tác quản lý tài xế
    path('them-tai-xe', taixe_views.them_tai_xe, name='them_tai_xe'),
    path('sua-tai-xe/<str:pk>/', taixe_views.sua_tai_xe, name='sua_tai_xe'),
    path('xoa-tai-xe/<str:pk>/', taixe_views.xoa_tai_xe, name='xoa_tai_xe'),

]
