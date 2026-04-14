from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
import requests

# ==================== NHÀ XE (Quản lý Tài Xế) ====================

def quanlytaixe(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('index')
    
    # Ở file HTML (quanlytaixe.html) bạn đã xử lý gọi API bằng fetch (client-side) để lấy danh sách, 
    # thêm, sửa, xóa tài xế. Do đó ở file view này chỉ cần render HTML là đủ.
    # Trong tương lai nếu muốn chuyển logic gọi API lên Server-side (Django View) 
    # thì sẽ viết logic requests.get/post/put/delete ở đây.
    
    return render(request, 'home/quanlytaixe.html')

# ==================== TÀI XẾ (Màn hình của chính Tài Xế) ====================

def taixe(request):
    return render(request, 'home/taixe.html')

def thongtin_taixe(request):
    return render(request, 'home/thongtin_taixe.html')

def taixe_lotrinh(request):
    return render(request, 'home/taixe_lotrinh.html')

def phancongtaixe(request):
    return render(request, 'home/phancongtaixe.html')