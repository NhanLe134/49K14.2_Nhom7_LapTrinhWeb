from datetime import datetime
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Ve

def quanlyve(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('dangnhap')
        
    try:
        # Lấy toàn bộ vé của khách hàng
        ve_list_all = Ve.objects.filter(KhachHang_id=user_id).select_related(
            'ChuyenXe', 'ChuyenXe__TuyenXe', 'ChuyenXe__Xe__Nhaxe', 'Ghe'
        ).order_by('-NgayDat')
        
        ve_da_dat = []
        ve_da_di = []
        ve_da_huy = []
        
        today = datetime.now().date()
        
        # Lấy ID các vé đã đánh giá
        from .models import DanhGia
        ve_da_danh_gia_ids = list(DanhGia.objects.filter(KhachHang_id=user_id).values_list('Ve_id', flat=True))

        for v in ve_list_all:
            v.da_danh_gia = v.VeID in ve_da_danh_gia_ids
            # Tự động cập nhật vé thành 'Đã đi' chỉ khi chuyến xe đã hoàn thành
            if v.TrangThai == 'Đã đặt' and v.ChuyenXe and v.ChuyenXe.TrangThai == 'Hoàn thành':
                v.TrangThai = 'Đã đi'
                v.save(update_fields=['TrangThai'])

            # Phân loại vé dựa trên trường TrangThai mới
            if v.TrangThai == 'Đã hủy':
                ve_da_huy.append(v)
            elif v.TrangThai == 'Đã đi':
                ve_da_di.append(v)
            else:
                ve_da_dat.append(v)
                
        return render(request, 'home/quanlyve.html', {
            've_da_dat': ve_da_dat,
            've_da_di': ve_da_di,
            've_da_huy': ve_da_huy,
        })
    except Exception as e:
        messages.error(request, f"Lỗi lấy danh sách vé: {str(e)}")
        return render(request, 'home/quanlyve.html', {
            've_da_dat': [], 
            've_da_di': [], 
            've_da_huy': []
        })
