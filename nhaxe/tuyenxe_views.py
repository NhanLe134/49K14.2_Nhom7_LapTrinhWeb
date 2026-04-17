from django.shortcuts import render, redirect
from django.contrib import messages
from .models import TuyenXe, Nhaxe, ChuyenXe

def quanlytuyenxe(request):
    nha_xe_id = request.session.get('user_id')
    if not nha_xe_id:
        return redirect('index')

    try:
        # Lấy danh sách tuyến xe trực tiếp từ Database
        danh_sach_tuyen = TuyenXe.objects.filter(nhaXe_id=nha_xe_id)
        
        # Danh sách tên tuyến để gợi ý hoặc kiểm tra (nếu cần)
        tat_ca_ten_tuyen = list(TuyenXe.objects.values_list('tenTuyen', flat=True))
        
        # Tính toán ID mới
        import re
        all_ids = TuyenXe.objects.values_list('tuyenXeID', flat=True)
        max_id = 0
        for tx_id in all_ids:
            if tx_id and tx_id.startswith('TX') and tx_id[2:].isdigit():
                num = int(tx_id[2:])
                if num > max_id:
                    max_id = num
        
        ma_tuyen_xe_moi = f"TX{max_id + 1:04d}"

        context = {
            'nha_xe_id': nha_xe_id,
            'danh_sach_tuyen': danh_sach_tuyen,
            'ma_tuyen_xe_moi': ma_tuyen_xe_moi
        }
        return render(request, 'home/quanlytuyenxe.html', context)
    except Exception as e:
        messages.error(request, f'Lỗi lấy dữ liệu tuyến xe: {str(e)}')
        return render(request, 'home/quanlytuyenxe.html', {'danh_sach_tuyen': []})

def them_tuyen_xe(request):
    if request.method == 'POST':
        nha_xe_id = request.session.get('user_id')
        if not nha_xe_id:
            return redirect('index')

        ten_tuyen = request.POST.get('tenTuyen')
        diem_di = request.POST.get('diemDi')
        diem_den = request.POST.get('diemDen')
        quang_duong = request.POST.get('quangDuong')
        diem_trung_gian = request.POST.get('diemTrungGian')
        
        try:
            # 1. Tính ID mới
            all_ids = TuyenXe.objects.values_list('tuyenXeID', flat=True)
            max_id = 0
            for tx_id in all_ids:
                if tx_id and tx_id.startswith('TX') and tx_id[2:].isdigit():
                    num = int(tx_id[2:])
                    if num > max_id:
                        max_id = num
            next_id = f"TX{max_id + 1:04d}"

            # 2. Lưu vào Database
            nha_xe_obj = Nhaxe.objects.get(NhaxeID=nha_xe_id)
            TuyenXe.objects.create(
                tuyenXeID=next_id,
                nhaXe=nha_xe_obj,
                tenTuyen=ten_tuyen,
                diemDi=diem_di,
                diemDen=diem_den,
                QuangDuong=quang_duong if quang_duong else None,
                DiemTrungGian=diem_trung_gian if diem_trung_gian else None
            )
            messages.success(request, 'Thêm tuyến xe thành công')
        except Exception as e:
            messages.error(request, f'Lỗi khi thêm tuyến xe: {str(e)}')
            
    return redirect('quanlytuyenxe')

def sua_tuyen_xe(request, pk):
    if request.method == 'POST':
        ten_tuyen = request.POST.get('tenTuyen')
        diem_di = request.POST.get('diemDi')
        diem_den = request.POST.get('diemDen')
        quang_duong = request.POST.get('quangDuong')
        diem_trung_gian = request.POST.get('diemTrungGian')
        
        try:
            TuyenXe.objects.filter(tuyenXeID=pk).update(
                tenTuyen=ten_tuyen,
                diemDi=diem_di,
                diemDen=diem_den,
                QuangDuong=quang_duong if quang_duong else None,
                DiemTrungGian=diem_trung_gian if diem_trung_gian else None
            )
            messages.success(request, 'Cập nhật tuyến xe thành công')
        except Exception as e:
            messages.error(request, f'Lỗi khi cập nhật: {str(e)}')
            
    return redirect('quanlytuyenxe')

def xoa_tuyen_xe(request, pk):
    if request.method == 'POST':
        try:
            # Kiểm tra xem có chuyến xe nào đang sử dụng tuyến này không
            if ChuyenXe.objects.filter(TuyenXe_id=pk).exists():
                messages.error(request, 'Không thể xóa tuyến xe, có chuyến đang hoạt động')
                return redirect('quanlytuyenxe')

            TuyenXe.objects.filter(tuyenXeID=pk).delete()
            messages.success(request, 'Xóa tuyến xe thành công')
        except Exception as e:
            messages.error(request, f'Lỗi khi xóa: {str(e)}')
            
    return redirect('quanlytuyenxe')
