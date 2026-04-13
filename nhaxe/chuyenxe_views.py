from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
import requests
import uuid

# ==================== NHÀ XE (nx) ====================

def quanlychuyenxe(request):
    user_id = request.session.get('user_id')
    chuyen_xe_list = []
    if user_id:
        headers = {'Authorization': f"Bearer {request.session.get('token', '')}"}
        try:
            api_url = f"{settings.API_BASE_URL}/api/chuyenxe/"
            response = requests.get(api_url, headers=headers, timeout=settings.API_TIMEOUT)
            if response.status_code == 200:
                chuyen_xe_list = response.json()
        except requests.exceptions.RequestException:
            pass
    return render(request, 'home/quanlychuyenxe.html', {'chuyen_xe_list': chuyen_xe_list})

def themchuyenxe(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('index')
        
    headers = {'Authorization': f"Bearer {request.session.get('token', '')}"}
    
    if request.method == 'POST':
        payload = {
            'tuyenXeId': request.POST.get('tuyenxe'),
            'xeId': request.POST.get('xe'),
            'taixeId': request.POST.get('taixe'),
            'ngayKhoiHanh': request.POST.get('date'),
            'gioDi': request.POST.get('time'),
            'nhaXeId': user_id,
            'trangThai': 'Đang chờ'
        }
        try:
            api_url = f"{settings.API_BASE_URL}/api/chuyenxe"
            response = requests.post(api_url, json=payload, headers=headers, timeout=settings.API_TIMEOUT)
            if response.status_code in [200, 201]:
                messages.success(request, 'Thêm chuyến xe thành công.')
            else:
                messages.error(request, f'Thêm chuyến xe thất bại (Lỗi {response.status_code}).')
        except requests.exceptions.RequestException:
            messages.error(request, 'Lỗi kết nối API.')
        # Cố tình không redirect để hiển thị lại form trống như yêu cầu của user

    # GET request - Lấy options cho dropdown
    tuyen_xe_list, xe_list, taixe_list = [], [], []
    try:
        req_tuyen = requests.get(f"{settings.API_BASE_URL}/api/tuyenxe/", headers=headers, timeout=settings.API_TIMEOUT)
        if req_tuyen.status_code == 200: tuyen_xe_list = req_tuyen.json()
        
        req_xe = requests.get(f"{settings.API_BASE_URL}/api/xe/", headers=headers, timeout=settings.API_TIMEOUT)
        if req_xe.status_code == 200: xe_list = req_xe.json()
        
        req_taixe = requests.get(f"{settings.API_BASE_URL}/api/taixe/", headers=headers, timeout=settings.API_TIMEOUT)
        if req_taixe.status_code == 200: taixe_list = req_taixe.json()
    except requests.exceptions.RequestException:
        pass
    
    return render(request, 'home/themchuyenxe.html', {
        'tuyen_xe_list': tuyen_xe_list,
        'xe_list': xe_list,
        'taixe_list': taixe_list
    })

def suachuyenxe(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('index')

    headers = {'Authorization': f"Bearer {request.session.get('token', '')}"}

    if request.method == 'POST':
        chuyenxe_id = request.POST.get('id')
        payload = {
            'chuyenXeId': chuyenxe_id,
            'tuyenXeId': request.POST.get('tuyenxe'),
            'xeId': request.POST.get('xe'),
            'taixeId': request.POST.get('taixe'),
            'ngayKhoiHanh': request.POST.get('date'),
            'gioDi': request.POST.get('time')
        }
        try:
            api_url = f"{settings.API_BASE_URL}/api/chuyenxe/{chuyenxe_id}"
            response = requests.put(api_url, json=payload, headers=headers, timeout=settings.API_TIMEOUT)
            if response.status_code in [200, 204]:
                messages.success(request, 'Sửa chuyến xe thành công.')
            else:
                messages.error(request, f'Sửa chuyến xe thất bại (Lỗi {response.status_code}): {response.text}')
        except requests.exceptions.RequestException:
            messages.error(request, 'Lỗi kết nối API lấy dữ liệu.')
        return redirect('quanlychuyenxe')

    chuyenxe_id = request.GET.get('id')
    if not chuyenxe_id:
        return redirect('quanlychuyenxe')

    chuyen = None
    tuyen_xe_list, xe_list, taixe_list = [], [], []
    try:
        req_chuyen = requests.get(f"{settings.API_BASE_URL}/api/chuyenxe/{chuyenxe_id}", headers=headers, timeout=settings.API_TIMEOUT)
        if req_chuyen.status_code == 200:
            chuyen = req_chuyen.json()
            
        req_tuyen = requests.get(f"{settings.API_BASE_URL}/api/tuyenxe/", headers=headers, timeout=settings.API_TIMEOUT)
        if req_tuyen.status_code == 200: tuyen_xe_list = req_tuyen.json()
        
        req_xe = requests.get(f"{settings.API_BASE_URL}/api/xe/", headers=headers, timeout=settings.API_TIMEOUT)
        if req_xe.status_code == 200: xe_list = req_xe.json()
        
        req_taixe = requests.get(f"{settings.API_BASE_URL}/api/taixe/", headers=headers, timeout=settings.API_TIMEOUT)
        if req_taixe.status_code == 200: taixe_list = req_taixe.json()
    except requests.exceptions.RequestException:
        pass

    if not chuyen:
        messages.error(request, 'Không tìm thấy chuyến xe này hoặc lỗi kết nối.')
        return redirect('quanlychuyenxe')

    return render(request, 'home/suachuyenxe.html', {
        'chuyen': chuyen,
        'tuyen_xe_list': tuyen_xe_list,
        'xe_list': xe_list,
        'taixe_list': taixe_list
    })

# ==================== TÀI XẾ (tx) ====================

def taixe_quanlychuyenxe(request):
    user_id = request.session.get('user_id')
    chuyen_xe_list = []
    if user_id:
        headers = {'Authorization': f"Bearer {request.session.get('token', '')}"}
        try:
            api_url = f"{settings.API_BASE_URL}/api/chuyenxe/"
            response = requests.get(api_url, headers=headers, timeout=settings.API_TIMEOUT)
            if response.status_code == 200:
                chuyen_xe_list = [c for c in response.json() if str(c.get('Taixe')).strip() == str(user_id)]
        except requests.exceptions.RequestException:
            pass
    return render(request, 'home/taixe_quanlychuyenxe.html', {'chuyen_xe_list': chuyen_xe_list})

def taixe_chitietchuyenxe(request):
    headers = {'Authorization': f"Bearer {request.session.get('token', '')}"}
    
    if request.method == 'POST':
        chuyenxe_id = request.POST.get('id')
        new_status = request.POST.get('status')
        if chuyenxe_id and new_status:
            payload = {'trangThai': new_status}
            try:
                api_url = f"{settings.API_BASE_URL}/api/chuyenxe/{chuyenxe_id}/status"
                response = requests.put(api_url, json=payload, headers=headers, timeout=settings.API_TIMEOUT)
                if response.status_code in [200, 204]:
                    messages.success(request, 'Cập nhật trạng thái thành công.')
                else:
                    messages.error(request, 'Cập nhật trạng thái thất bại trên server.')
            except requests.exceptions.RequestException:
                messages.error(request, 'Lỗi kết nối API Server.')
            return redirect(f"/taixe_chitietchuyenxe?id={chuyenxe_id}")
            
    chuyenxe_id = request.GET.get('id')
    if chuyenxe_id:
        try:
            api_url = f"{settings.API_BASE_URL}/api/chuyenxe/{chuyenxe_id}"
            response = requests.get(api_url, headers=headers, timeout=settings.API_TIMEOUT)
            if response.status_code == 200:
                chuyen = response.json()
                return render(request, 'home/taixe_chitietchuyenxe.html', {'chuyen': chuyen})
        except requests.exceptions.RequestException:
            pass
            
    return redirect('taixe_quanlychuyenxe')
