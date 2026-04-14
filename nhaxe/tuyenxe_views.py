from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
import requests
import json

def quanlytuyenxe(request):
    nha_xe_id = request.session.get('user_id')

    danh_sach_tuyen = []
    tat_ca_ten_tuyen = []
    
    response = requests.get(f"{settings.API_BASE_URL}/api/tuyenxe/")
    if response.status_code == 200:
        tat_ca_tuyen = response.json()
        
        for tuyen in tat_ca_tuyen:
            if tuyen.get('tenTuyen'):
                tat_ca_ten_tuyen.append(tuyen.get('tenTuyen'))
                
            nha_xe_cua_tuyen = tuyen.get('nhaXe')
            
            if nha_xe_cua_tuyen == nha_xe_id:
                danh_sach_tuyen.append(tuyen)
    else:
        messages.error(request, 'Lỗi hệ thống. Vui lòng thử lại sau.')
        
    context = {
        'nha_xe_id': nha_xe_id,
        'danh_sach_tuyen': danh_sach_tuyen,
        'tat_ca_ten_tuyen_json': json.dumps(tat_ca_ten_tuyen)
    }
    return render(request, 'home/quanlytuyenxe.html', context)

def them_tuyen_xe(request):
    if request.method == 'POST':
        nha_xe_id = request.session.get('user_id')

        ten_tuyen = request.POST.get('tenTuyen')
        diem_di = request.POST.get('diemDi')
        diem_den = request.POST.get('diemDen')
        quang_duong = request.POST.get('quangDuong')
        diem_trung_gian = request.POST.get('diemTrungGian')
        
        response_get = requests.get(f"{settings.API_BASE_URL}/api/tuyenxe/")
        max_id = 0
        if response_get.status_code == 200:
            tat_ca_tuyen = response_get.json()
            for tuyen in tat_ca_tuyen:
                tx_id = tuyen.get('tuyenXeID', '')
                if tx_id and tx_id.startswith('TX') and tx_id[2:].isdigit():
                    num = int(tx_id[2:])
                    if num > max_id:
                        max_id = num
        
        next_id = f"TX{max_id + 1:04d}"

        payload = {
            "tuyenXeID": next_id,
            "tenTuyen": ten_tuyen,
            "diemDi": diem_di,
            "diemDen": diem_den,
            "QuangDuong": quang_duong if quang_duong else None,
            "DiemTrungGian": diem_trung_gian if diem_trung_gian else None,
            "nhaXe": nha_xe_id
        }
        
        response = requests.post(f"{settings.API_BASE_URL}/api/tuyenxe/", json=payload)
        if response.status_code in [200, 201]:
            messages.success(request, 'Thêm tuyến xe thành công')
        else:
            messages.error(request, 'Lỗi hệ thống. Vui lòng thử lại sau.')
            
    return redirect('quanlytuyenxe')

def sua_tuyen_xe(request, pk):
    if request.method == 'POST':
        nha_xe_id = request.session.get('user_id')

        ten_tuyen = request.POST.get('tenTuyen')
        diem_di = request.POST.get('diemDi')
        diem_den = request.POST.get('diemDen')
        quang_duong = request.POST.get('quangDuong')
        diem_trung_gian = request.POST.get('diemTrungGian')
        
        payload = {
            "tuyenXeID": pk,
            "tenTuyen": ten_tuyen,
            "diemDi": diem_di,
            "diemDen": diem_den,
            "QuangDuong": quang_duong if quang_duong else None,
            "DiemTrungGian": diem_trung_gian if diem_trung_gian else None,
            "nhaXe": nha_xe_id
        }
        
        response = requests.put(f"{settings.API_BASE_URL}/api/tuyenxe/{pk}/", json=payload)
        if response.status_code in [200, 204]:
            messages.success(request, 'Cập nhật tuyến xe thành công')
        else:
            messages.error(request, 'Lỗi hệ thống. Vui lòng thử lại sau.')
            
    return redirect('quanlytuyenxe')

def xoa_tuyen_xe(request, pk):
    if request.method == 'POST':
        nha_xe_id = request.session.get('user_id')

        response_chuyen = requests.get(f"{settings.API_BASE_URL}/api/chuyenxe/")
        if response_chuyen.status_code == 200:
            tat_ca_chuyen = response_chuyen.json()
            for chuyen in tat_ca_chuyen:
                tuyen_cua_chuyen = chuyen.get('tuyenXe')
                if tuyen_cua_chuyen == pk or (isinstance(tuyen_cua_chuyen, dict) and tuyen_cua_chuyen.get('tuyenXeID') == pk):
                    messages.error(request, 'Không thể xóa tuyến xe, có chuyến đang hoạt động')
                    return redirect('quanlytuyenxe')

        response = requests.delete(f"{settings.API_BASE_URL}/api/tuyenxe/{pk}/")
        if response.status_code in [200, 204]:
            messages.success(request, 'Xóa tuyến xe thành công')
        else:
            messages.error(request, 'Lỗi hệ thống. Vui lòng thử lại sau.')
            
    return redirect('quanlytuyenxe')