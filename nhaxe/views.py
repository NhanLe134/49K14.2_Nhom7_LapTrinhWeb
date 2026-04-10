from django.shortcuts import render, redirect
from django.contrib import messages


# ==================== TRANG CHUNG ====================

def index(request):
    return render(request, 'home/index.html')


def timkiem(request):
    return render(request, 'home/timkiem.html')


def quen_mat_khau(request):
    return render(request, 'home/quen_mat_khau.html')


def dangky_khachhang(request):
    return render(request, 'home/dangky_khachhang.html')


def dangky_nhaxe(request):
    return render(request, 'home/dangky_nhaxe.html')


# ==================== KHÁCH HÀNG (kh) ====================

def khachhang(request):
    return render(request, 'home/khachhang.html')


def thongtin_khachhang(request):
    return render(request, 'home/thongtin_khachhang.html')


def lotrinh(request):
    return render(request, 'home/lotrinh.html')


def chitietchuyenxe(request):
    return render(request, 'home/chitietchuyenxe.html')


def vecuatoi(request):
    return render(request, 'home/vecuatoi.html')


def vietdanhgia(request):
    return render(request, 'home/vietdanhgia.html')


def dadanhgia(request):
    return render(request, 'home/dadanhgia.html')


def danhgiachuyenxe(request):
    return render(request, 'home/danhgiachuyenxe.html')


# ==================== NHÀ XE (nx) ====================

def nhaxe(request):
    return render(request, 'home/nhaxe.html')

def thong_tin_nha_xe(request):
    return render(request, 'home/thong_tin_nha_xe.html')

def quanlychuyenxe(request):
    return render(request, 'home/quanlychuyenxe.html')

def themchuyenxe(request):
    return render(request, 'home/themchuyenxe.html')

def suachuyenxe(request):
    return render(request, 'home/suachuyenxe.html')

def quanlytuyenxe(request):
    return render(request, 'home/quanlytuyenxe.html')

def quanly_loaixe(request):
    return render(request, 'home/quanly_loaixe.html')

def quan_ly_xe(request):
    return render(request, 'home/quan_ly_xe.html')

def quanlytaixe(request):
    return render(request, 'home/quanlytaixe.html')

def quanly_khachhang(request):
    return render(request, 'home/quanly_khachhang.html')

def quanlyve(request):
    return render(request, 'home/quanlyve.html')

# ==================== TÀI XẾ (tx) ====================

def taixe(request):
    return render(request, 'home/taixe.html')

def thongtin_taixe(request):
    return render(request, 'home/thongtin_taixe.html')

def taixe_quanlychuyenxe(request):
    return render(request, 'home/taixe_quanlychuyenxe.html')

def taixe_chitietchuyenxe(request):
    return render(request, 'home/taixe_chitietchuyenxe.html')

def taixe_lotrinh(request):
    return render(request, 'home/taixe_lotrinh.html')

def phancongtaixe(request):
    return render(request, 'home/phancongtaixe.html')