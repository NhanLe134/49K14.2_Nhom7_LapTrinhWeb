from django.urls import path
from . import views
from . import auth_views
from . import chuyenxe_views
from . import taixe_views
from . import tuyenxe_views
from . import xuly_timkiem_view
from . import booking_views
from . import quanlyve_views

urlpatterns = [

    # ==================== TRANG CHUNG ====================
    path('', auth_views.index, name='index'),
    path('dangnhap', auth_views.dangnhap, name='dangnhap'),
    path('dangxuat', auth_views.dangxuat, name='dangxuat'),
    path('timkiem', xuly_timkiem_view.view_tim_kiem_ve, name='timkiem'),
    path('timkiem_ve', xuly_timkiem_view.view_tim_kiem_ve, name='view_tim_kiem_ve'),
    path('api/lay_so_do_ghe', xuly_timkiem_view.lay_so_do_ghe_api, name='api_lay_so_do_ghe'),
    path('quen_mat_khau', views.quen_mat_khau, name='quen_mat_khau'),

    # ==================== ĐẶT VÉ ====================
    path('dat_ve_thong_tin', booking_views.dat_ve_thong_tin, name='dat_ve_thong_tin'),
    path('xac_nhan_dat_ve', booking_views.xac_nhan_dat_ve, name='xac_nhan_dat_ve'),
    path('huy-ve/<str:ve_id>/', booking_views.huy_ve, name='huy_ve'),

    # ==================== KHÁCH HÀNG ====================
    path('dangky_khachhang', views.dangky_khachhang, name='dangky_khachhang'),
    path('khachhang', views.khachhang, name='khachhang'),
    path('thongtin_khachhang', views.thongtin_khachhang, name='thongtin_khachhang'),
    path('dadanhgia', views.dadanhgia, name='dadanhgia'),
    path('danhgiachuyenxe', views.danhgiachuyenxe, name='danhgiachuyenxe'),
    path('quanlyve', quanlyve_views.quanlyve, name='quanlyve'),
    path('vietdanhgia', views.vietdanhgia, name='vietdanhgia'),

    # ==================== NHÀ XE ====================
    path('dangky_nhaxe', views.dangky_nhaxe, name='dangky_nhaxe'),
    path('nhaxe', views.nhaxe, name='nhaxe'),
    path('thong_tin_nha_xe', views.thong_tin_nha_xe, name='thong_tin_nha_xe'),
    path('quanly_khachhang', views.quanly_khachhang, name='quanly_khachhang'),
    path('quan_ly_xe', views.quan_ly_xe, name='quan_ly_xe'),
    path('quanly_loaixe', views.quanly_loaixe, name='quanly_loaixe'),
    
    # --- Chuyến xe (Nhà xe) ---
    path('quanlychuyenxe', chuyenxe_views.quanlychuyenxe, name='quanlychuyenxe'),
    path('themchuyenxe', chuyenxe_views.themchuyenxe, name='themchuyenxe'),
    path('chitietchuyenxe', views.chitietchuyenxe, name='chitietchuyenxe'),
    path('suachuyenxe', chuyenxe_views.suachuyenxe, name='suachuyenxe'),
    path('lotrinh', views.lotrinh, name='lotrinh'),
    path('quanlytuyenxe', tuyenxe_views.quanlytuyenxe, name='quanlytuyenxe'),

    # --- Tài xế (Nhà xe quản lý) ---
    path('quanlytaixe', taixe_views.quanlytaixe, name='quanlytaixe'),
    path('them-tai-xe', taixe_views.them_tai_xe, name='them_tai_xe'),
    path('sua-tai-xe/<str:pk>/', taixe_views.sua_tai_xe, name='sua_tai_xe'),
    path('xoa-tai-xe/<str:pk>/', taixe_views.xoa_tai_xe, name='xoa_tai_xe'),


    # ==================== TÀI XẾ (Driver View) ====================
    path('taixe', taixe_views.taixe, name='taixe'),
    path('thongtin_taixe', taixe_views.thongtin_taixe, name='thongtin_taixe'),
    path('taixe_quanlychuyenxe', chuyenxe_views.taixe_quanlychuyenxe, name='taixe_quanlychuyenxe'),
    path('taixe_chitietchuyenxe', chuyenxe_views.taixe_chitietchuyenxe, name='taixe_chitietchuyenxe'),
    path('taixe_lotrinh', taixe_views.taixe_lotrinh, name='taixe_lotrinh'),
    path('phancongtaixe', taixe_views.phancongtaixe, name='phancongtaixe'),

]