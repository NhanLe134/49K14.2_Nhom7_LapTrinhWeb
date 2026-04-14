from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
import requests

def quanlytuyenxe(request):
    # Lấy đúng mã nhà xe từ session, không dùng mock data NX00001
    nha_xe_id = request.session.get('nha_xe_id')
    if not nha_xe_id:
        messages.error(request, 'Vui lòng đăng nhập để xem quản lý tuyến xe.')
        return redirect('dangnhap')

    danh_sach_tuyen = []
    
    try:
        response = requests.get(f"{settings.API_BASE_URL}/api/tuyenxe/")
        if response.status_code == 200:
            tat_ca_tuyen = response.json()
            
            for tuyen in tat_ca_tuyen:
                nha_xe_cua_tuyen = tuyen.get('nhaXe')
                
                if nha_xe_cua_tuyen == nha_xe_id:
                    danh_sach_tuyen.append(tuyen)
                elif isinstance(nha_xe_cua_tuyen, str) and nha_xe_cua_tuyen.strip() == nha_xe_id.strip():
                    danh_sach_tuyen.append(tuyen)
                elif isinstance(nha_xe_cua_tuyen, dict):
                    if nha_xe_id in list(nha_xe_cua_tuyen.values()):
                        danh_sach_tuyen.append(tuyen)
        else:
            messages.error(request, 'Không thể lấy dữ liệu tuyến xe từ máy chủ!')
    except requests.exceptions.RequestException as e:
        messages.error(request, f'Lỗi kết nối API: {str(e)}')
        
    context = {
        'nha_xe_id': nha_xe_id,
        'danh_sach_tuyen': danh_sach_tuyen
    }
    return render(request, 'home/quanlytuyenxe.html', context)

def them_tuyen_xe(request):
    if request.method == 'POST':
        nha_xe_id = request.session.get('nha_xe_id')
        if not nha_xe_id:
            messages.error(request, 'Vui lòng đăng nhập để thực hiện chức năng này.')
            return redirect('dangnhap')

        ten_tuyen = request.POST.get('tenTuyen')
        diem_di = request.POST.get('diemDi')
        diem_den = request.POST.get('diemDen')
        quang_duong = request.POST.get('quangDuong')
        diem_trung_gian = request.POST.get('diemTrungGian')
        
        if not ten_tuyen:
            ten_tuyen = f"{diem_di} - {diem_den}"
            
        try:
            # 1. Gọi API để lấy danh sách tuyến xe hiện tại và tìm mã lớn nhất
            response_get = requests.get(f"{settings.API_BASE_URL}/api/tuyenxe/")
            max_id = 0
            if response_get.status_code == 200:
                tat_ca_tuyen = response_get.json()
                for tuyen in tat_ca_tuyen:
                    tx_id = tuyen.get('tuyenXeID', '')
                    if tx_id and tx_id.startswith('TX'):
                        try:
                            num = int(tx_id[2:])
                            if num > max_id:
                                max_id = num
                        except ValueError:
                            pass
            
            # 2. Tạo mã mới TX + số thứ tự (vd TX0004)
            next_id = f"TX{max_id + 1:04d}"

            # 3. Thêm trường tuyenXeID vào payload gửi lên API
            payload = {
                "tuyenXeID": next_id,
                "tenTuyen": ten_tuyen,
                "diemDi": diem_di,
                "diemDen": diem_den,
                "QuangDuong": quang_duong if quang_duong else None,
                "DiemTrungGian": diem_trung_gian if diem_trung_gian else None,
                "nhaXe": nha_xe_id
            }
            
            # 4. Gửi request POST
            response = requests.post(f"{settings.API_BASE_URL}/api/tuyenxe/", json=payload)
            if response.status_code in [200, 201]:
                messages.success(request, f'Thêm tuyến mới thành công (Mã: {next_id})!')
            else:
                # Hiển thị chi tiết lỗi để dễ debug
                messages.error(request, f'Thêm thất bại. Mã lỗi: {response.status_code}. Chi tiết: {response.text}')
        except requests.exceptions.RequestException as e:
            messages.error(request, f'Lỗi kết nối API: {str(e)}')
            
    return redirect('quanlytuyenxe')

def sua_tuyen_xe(request, pk):
    if request.method == 'POST':
        nha_xe_id = request.session.get('nha_xe_id')
        if not nha_xe_id:
            messages.error(request, 'Vui lòng đăng nhập để thực hiện chức năng này.')
            return redirect('dangnhap')

        ten_tuyen = request.POST.get('tenTuyen')
        diem_di = request.POST.get('diemDi')
        diem_den = request.POST.get('diemDen')
        quang_duong = request.POST.get('quangDuong')
        diem_trung_gian = request.POST.get('diemTrungGian')
        
        if not ten_tuyen:
            ten_tuyen = f"{diem_di} - {diem_den}"
            
        payload = {
            "tuyenXeID": pk,
            "tenTuyen": ten_tuyen,
            "diemDi": diem_di,
            "diemDen": diem_den,
            "QuangDuong": quang_duong if quang_duong else None,
            "DiemTrungGian": diem_trung_gian if diem_trung_gian else None,
            "nhaXe": nha_xe_id
        }
        
        try:
            response = requests.put(f"{settings.API_BASE_URL}/api/tuyenxe/{pk}/", json=payload)
            if response.status_code in [200, 204]:
                messages.success(request, 'Cập nhật tuyến thành công!')
            else:
                messages.error(request, f'Cập nhật thất bại. Mã lỗi: {response.status_code}. Chi tiết: {response.text}')
        except requests.exceptions.RequestException as e:
            messages.error(request, f'Lỗi kết nối API: {str(e)}')
            
    return redirect('quanlytuyenxe')

def xoa_tuyen_xe(request, pk):
    if request.method == 'POST':
        nha_xe_id = request.session.get('nha_xe_id')
        if not nha_xe_id:
            messages.error(request, 'Vui lòng đăng nhập để thực hiện chức năng này.')
            return redirect('dangnhap')

        try:
            response = requests.delete(f"{settings.API_BASE_URL}/api/tuyenxe/{pk}/")
            if response.status_code in [200, 204]:
                messages.success(request, 'Xóa tuyến thành công!')
            else:
                messages.error(request, f'Xóa thất bại. Mã lỗi: {response.status_code}. Chi tiết: {response.text}')
        except requests.exceptions.RequestException as e:
            messages.error(request, f'Lỗi kết nối API: {str(e)}')
            
    return redirect('quanlytuyenxe')