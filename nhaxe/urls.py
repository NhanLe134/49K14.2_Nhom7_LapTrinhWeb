from django.urls import path
from . import views
from . import auth_views
from . import chuyenxe_views
from . import taixe_views
from . import tuyenxe_views
from . import xuly_timkiem_view
from . import feedback_views
from . import payment_views
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

    # ==================== ĐẶT VÉ & QUẢN LÝ VÉ ====================
    path('dat_ve_thong_tin', booking_views.dat_ve_thong_tin, name='dat_ve_thong_tin'),
    path('xac_nhan_dat_ve', booking_views.xac_nhan_dat_ve, name='xac_nhan_dat_ve'),
    path('dat-ve/thong-tin', booking_views.dat_ve_thong_tin, name='dat_ve_thong_tin_alt'),  # Giữ alias
    path('dat-ve/xac-nhan', booking_views.xac_nhan_dat_ve, name='xac_nhan_dat_ve_alt'),
    path('huy-ve/<str:ve_id>/', booking_views.huy_ve, name='huy_ve'),
    path('quanlyve/', quanlyve_views.quanlyve, name='quanlyve'),

    # ==================== OTP & ĐĂNG KÝ (ƯU TIÊN FILE 1) ====================
    path('dangky_khachhang', views.dangky_khachhang, name='dangky_khachhang'),
    path('send_registration_otp', views.send_registration_otp, name='send_registration_otp'),
    path('verify_and_register', views.verify_and_register, name='verify_and_register'),
    path('dangky_nhaxe', views.dangky_nhaxe, name='dangky_nhaxe'),
    path('send_registration_otp_nhaxe', views.send_registration_otp_nhaxe, name='send_registration_otp_nhaxe'),
    path('verify_and_register_nhaxe', views.verify_and_register_nhaxe, name='verify_and_register_nhaxe'),

    # ==================== KHÁCH HÀNG (ƯU TIÊN FILE 1) ====================
    path('khachhang', views.khachhang, name='khachhang'),
    path('thongtin_khachhang', views.thongtin_khachhang, name='thongtin_khachhang'),
    path('capnhat_thongtin_khachhang', views.capnhat_thongtin_khachhang, name='capnhat_thongtin_khachhang'),
    path('send_update_otp_khachhang', views.send_update_otp_khachhang, name='send_update_otp_khachhang'),
    path('lotrinh', views.lotrinh, name='lotrinh'),
    path('chitietchuyenxe', views.chitietchuyenxe, name='chitietchuyenxe'),
    path('vecuatoi', views.vecuatoi, name='vecuatoi'),
    # Bổ sung từ file 2
    path('khachhang/giao-dich/', payment_views.khachhang_lich_su_giao_dich, name='khachhang_giao_dich'),

    # ==================== THANH TOÁN (FILE 2 CÓ NHIỀU API HƠN) ====================
    path('payment/<str:ve_id>/', payment_views.process_payment, name='process_payment'),  # Cấu trúc file 1
    path('quanlyve/thanhtoan/<str:ve_id>/', payment_views.process_payment, name='process_payment_alt'),
    # Cấu trúc file 2
    path('confirm-payment/<str:ve_id>/', payment_views.confirm_payment, name='confirm_payment'),
    path('api/check-payment-status/<str:ve_id>/', payment_views.check_payment_status, name='check_payment_status'),
    path('payment/webhook/sepay/', payment_views.sepay_webhook, name='sepay_webhook'),

    # ==================== ĐÁNH GIÁ (FEEDBACK) ====================
    path('danhgiachuyenxe/', feedback_views.danhgiachuyenxe, name='danhgiachuyenxe'),
    path('danhgiachuyenxe/pending/', feedback_views.danhgiachuyenxe, {'tab': 'pending'},
         name='danhgiachuyenxe_pending'),
    path('danhgiachuyenxe/dadanhgia/', feedback_views.danhgiachuyenxe, {'tab': 'evaluated'}, name='dadanhgia'),
    path('danhgiachuyenxe/themdanhgia/<str:ve_id>/', feedback_views.vietdanhgia, name='themdanhgia'),
    path('danhgiachuyenxe/suadanhgia/<str:ve_id>/', feedback_views.vietdanhgia, name='suadanhgia'),
    path('submit_danhgia/', feedback_views.submit_danhgia, name='submit_danhgia'),

    # ==================== NHÀ XE (ƯU TIÊN FILE 1 CHO LOẠI XE) ====================
    path('nhaxe', views.nhaxe, name='nhaxe'),
    path('thong_tin_nha_xe', views.thong_tin_nha_xe, name='thong_tin_nha_xe'),
    path('quanly_khachhang', views.quanly_khachhang, name='quanly_khachhang'),
    path('quan_ly_xe', views.quan_ly_xe, name='quan_ly_xe'),
    path('quanly_loaixe', views.quanly_loaixe, name='quanly_loaixe'),
    path('cap-nhat-gia/<str:pk>/', views.capnhat_gia_loaixe, name='cap_nhat_gia_ve'),  # Cập nhật giá loại xe

    # Bổ sung quản lý tài chính nhà xe từ file 2
    path('nhaxe/cau-hinh-ngan-hang/', payment_views.nhaxe_cau_hinh_ngan_hang, name='nhaxe_cau_hinh_ngan_hang'),
    path('nhaxe/bao--cao-doanh-thu/', payment_views.nhaxe_bao_cao_doanh_thu, name='nhaxe_bao_cao_doanh_thu'),

    # ==================== CHUYẾN XE & TUYẾN XE (NHÀ XE) ====================
    path('quanlychuyenxe', chuyenxe_views.quanlychuyenxe, name='quanlychuyenxe'),
    path('themchuyenxe', chuyenxe_views.themchuyenxe, name='themchuyenxe'),
    path('suachuyenxe/<str:pk>/', chuyenxe_views.suachuyenxe, name='suachuyenxe'),
    path('hoanthanh-chuyenxe/<str:pk>/', chuyenxe_views.hoanthanh_chuyenxe, name='hoanthanh_chuyenxe'),

    path('quanlytuyenxe', tuyenxe_views.quanlytuyenxe, name='quanlytuyenxe'),
    path('them-tuyen-xe', tuyenxe_views.them_tuyen_xe, name='them_tuyen_xe'),
    path('sua-tuyen-xe/<str:pk>/', tuyenxe_views.sua_tuyen_xe, name='sua_tuyen_xe'),
    path('xoa-tuyen-xe/<str:pk>/', tuyenxe_views.xoa_tuyen_xe, name='xoa_tuyen_xe'),

    # ==================== QUẢN LÝ TÀI XẾ (NHÀ XE QUẢN LÝ) ====================
    path('quanlytaixe', taixe_views.quanlytaixe, name='quanlytaixe'),
    path('them-tai-xe', taixe_views.them_tai_xe, name='them_tai_xe'),
    path('sua-tai-xe/<str:pk>/', taixe_views.sua_tai_xe, name='sua_tai_xe'),
    path('xoa-tai-xe/<str:pk>/', taixe_views.xoa_tai_xe, name='xoa_tai_xe'),
    path('phancongtaixe', taixe_views.phancongtaixe, name='phancongtaixe'),

    # ==================== TÀI XẾ (GIAO DIỆN RIÊNG CHO TÀI XẾ) ====================
    path('taixe', taixe_views.taixe, name='taixe'),
    path('thongtin_taixe', taixe_views.thongtin_taixe, name='thongtin_taixe'),
    path('taixe_quanlychuyenxe', chuyenxe_views.taixe_quanlychuyenxe, name='taixe_quanlychuyenxe'),
    path('taixe_chitietchuyenxe', chuyenxe_views.taixe_chitietchuyenxe, name='taixe_chitietchuyenxe'),
    path('taixe_lotrinh', taixe_views.taixe_lotrinh, name='taixe_lotrinh'),

    # ==================== QUẢN TRỊ VIÊN (ADMIN - CHỈ CÓ Ở FILE 2) ====================
    path('admin/dashboard-quyet-toan/', payment_views.admin_dashboard_quyet_toan, name='admin_dashboard_quyet_toan'),
    path('admin/xac-nhan-quyet-toan/<str:nhaxe_id>/', payment_views.admin_xac_nhan_quyet_toan,
         name='admin_xac_nhan_quyet_toan'),
    path('admin/danh-sach-nhaxe/', payment_views.admin_list_nhaxe, name='admin_list_nhaxe'),
    path('admin/quan-ly-khachhang/', payment_views.admin_list_khachhang, name='admin_list_khachhang'),
]