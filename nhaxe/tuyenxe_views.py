from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import TuyenXe, Nhaxe, ChuyenXe
from datetime import datetime
from django.db import models


# ==================== TUYẾN XE ====================

def quanlytuyenxe(request):
    """
    Hiển thị danh sách tuyến xe của nhà xe
    """
    nha_xe_id = request.session.get('user_id')
    if not nha_xe_id:
        messages.error(request, "Vui lòng đăng nhập để xem quản lý tuyến xe.")
        return redirect('dangnhap')

    nha_xe_obj = get_object_or_404(Nhaxe, NhaxeID=nha_xe_id)

    # Thông báo chuyến trễ
    today = datetime.now().date()
    overdue_trips = ChuyenXe.objects.filter(
        NgayKhoiHanh__lt=today,
        TrangThai='Chưa hoàn thành'
    ).select_related('TuyenXe')
    
    overdue_trips_list = [trip for trip in overdue_trips if trip.TuyenXe and getattr(trip.TuyenXe, 'nhaXe_id', getattr(trip.TuyenXe, 'nhaxe_id', None)) == nha_xe_id]
    overdue_trips_count = len(overdue_trips_list)

    # Lấy danh sách tuyến
    danh_sach_tuyen_raw = TuyenXe.objects.all()
    danh_sach_tuyen = [tuyen for tuyen in danh_sach_tuyen_raw if getattr(tuyen, 'nhaXe_id', getattr(tuyen, 'nhaxe_id', None)) == nha_xe_id]

    # Tính toán số chuyến đang khai thác cho mỗi tuyến
    tuyen_data = []
    for tuyen in danh_sach_tuyen:
        # Số chuyến đang hoạt động
        so_chuyen = ChuyenXe.objects.filter(
            TuyenXe=tuyen,
            TrangThai__in=['Chưa hoàn thành', 'Đang chạy'] # Hoặc các trạng thái phù hợp
        ).count()
        
        tuyen_data.append({
            'tuyenXeID': tuyen.tuyenXeID,
            'tenTuyen': tuyen.tenTuyen,
            'diemDi': tuyen.diemDi,
            'diemDen': tuyen.diemDen,
            'QuangDuong': tuyen.QuangDuong,
            'ThoiGian': tuyen.ThoiGian,
            'so_chuyen': so_chuyen
        })

    return render(request, 'home/quanlytuyenxe.html', {
        'danh_sach_tuyen': tuyen_data,
        'nha_xe': nha_xe_obj,
        'avatar_url': getattr(nha_xe_obj, 'AnhDaiDienURL', None) if nha_xe_obj else None,
        'overdue_trips': overdue_trips_list,
        'overdue_trips_count': overdue_trips_count
    })

def them_tuyen_xe(request):
    """
    Xử lý thêm tuyến xe mới
    """
    if request.method == 'POST':
        nha_xe_id = request.session.get('user_id')
        if not nha_xe_id:
            messages.error(request, "Vui lòng đăng nhập để thêm tuyến xe.")
            return redirect('dangnhap')

        ten_tuyen = request.POST.get('ten_tuyen')
        diem_di = request.POST.get('diem_di')
        diem_den = request.POST.get('diem_den')
        quang_duong = request.POST.get('quang_duong')
        thoi_gian = request.POST.get('thoi_gian')

        # Validate
        if not all([ten_tuyen, diem_di, diem_den, quang_duong, thoi_gian]):
            messages.error(request, "Vui lòng điền đầy đủ thông tin.")
            return redirect('quanlytuyenxe')
            
        try:
            quang_duong = float(quang_duong)
            thoi_gian = float(thoi_gian)
        except ValueError:
            messages.error(request, "Quãng đường và Thời gian phải là số hợp lệ.")
            return redirect('quanlytuyenxe')

        try:
            nha_xe_obj = Nhaxe.objects.get(NhaxeID=nha_xe_id)
            
            # Tạo ID mới
            last_tuyen = TuyenXe.objects.order_by('tuyenXeID').last()
            new_id = "TX00001"
            if last_tuyen and last_tuyen.tuyenXeID.startswith("TX"):
                num = int(last_tuyen.tuyenXeID[2:]) + 1
                new_id = f"TX{num:05d}"

            # Lưu vào database. Phải cẩn thận với tên trường do CSDL đã đổi.
            # Dùng create với unpack dict để linh hoạt nếu field bị sai tên
            # kwargs = {
            #    'tuyenXeID': new_id,
            #    'tenTuyen': ten_tuyen,
            #    'diemDi': diem_di,
            #    'diemDen': diem_den,
            #    'QuangDuong': quang_duong,
            #    'ThoiGian': thoi_gian,
            # }
            # Nhưng ta phải gán object vào trường khóa ngoại
            tuyen = TuyenXe(
                tuyenXeID=new_id,
                tenTuyen=ten_tuyen,
                diemDi=diem_di,
                diemDen=diem_den,
                QuangDuong=quang_duong,
                ThoiGian=thoi_gian,
                nhaXe=nha_xe_obj # Django sẽ map sang field nhaXe_id hoặc tương đương
            )
            tuyen.save()

            messages.success(request, f"Đã thêm tuyến xe '{ten_tuyen}' thành công.")
        except Nhaxe.DoesNotExist:
            messages.error(request, "Không tìm thấy thông tin nhà xe.")
        except Exception as e:
            messages.error(request, f"Có lỗi xảy ra: {e}")

    return redirect('quanlytuyenxe')

def sua_tuyen_xe(request, pk):
    """
    Xử lý sửa tuyến xe
    """
    if request.method == 'POST':
        nha_xe_id = request.session.get('user_id')
        if not nha_xe_id:
            messages.error(request, "Vui lòng đăng nhập để sửa tuyến xe.")
            return redirect('dangnhap')

        try:
            tuyen_xe = get_object_or_404(TuyenXe, pk=pk)
            
            # Kiểm tra quyền: Tuyến xe này có thuộc về nhà xe đang đăng nhập không?
            if getattr(tuyen_xe, 'nhaXe_id', getattr(tuyen_xe, 'nhaxe_id', None)) != nha_xe_id:
                messages.error(request, "Bạn không có quyền sửa tuyến xe này.")
                return redirect('quanlytuyenxe')

            # Lấy dữ liệu từ form
            ten_tuyen = request.POST.get('ten_tuyen')
            diem_di = request.POST.get('diem_di')
            diem_den = request.POST.get('diem_den')
            quang_duong = request.POST.get('quang_duong')
            thoi_gian = request.POST.get('thoi_gian')

            # Validate cơ bản
            if not all([ten_tuyen, diem_di, diem_den, quang_duong, thoi_gian]):
                 messages.error(request, "Vui lòng điền đầy đủ thông tin.")
                 return redirect('quanlytuyenxe')

            # Cập nhật thông tin
            tuyen_xe.tenTuyen = ten_tuyen
            tuyen_xe.diemDi = diem_di
            tuyen_xe.diemDen = diem_den
            tuyen_xe.QuangDuong = float(quang_duong)
            tuyen_xe.ThoiGian = float(thoi_gian)
            tuyen_xe.save()

            messages.success(request, f"Đã cập nhật tuyến xe '{ten_tuyen}' thành công.")
        except ValueError:
             messages.error(request, "Dữ liệu Quãng đường/Thời gian không hợp lệ.")
        except Exception as e:
            messages.error(request, f"Lỗi: {e}")

    return redirect('quanlytuyenxe')


def xoa_tuyen_xe(request, pk):
    """
    Xử lý xóa tuyến xe (hoặc đánh dấu ngưng hoạt động nếu đã có chuyến)
    """
    if request.method == 'POST' or request.method == 'GET': # Hỗ trợ cả GET nếu gọi từ modal hoặc link trực tiếp (dù POST an toàn hơn)
        nha_xe_id = request.session.get('user_id')
        if not nha_xe_id:
             return JsonResponse({'status': 'error', 'message': 'Vui lòng đăng nhập.'})

        try:
            tuyen_xe = get_object_or_404(TuyenXe, pk=pk)
            
            if getattr(tuyen_xe, 'nhaXe_id', getattr(tuyen_xe, 'nhaxe_id', None)) != nha_xe_id:
                 return JsonResponse({'status': 'error', 'message': 'Bạn không có quyền xóa tuyến xe này.'})

            # Kiểm tra xem có chuyến xe nào đang tham chiếu đến tuyến này không
            chuyen_xe_dang_hoat_dong = ChuyenXe.objects.filter(TuyenXe=tuyen_xe).exists()
            
            if chuyen_xe_dang_hoat_dong:
                # Thay vì xóa cứng (gây lỗi foreign key), có thể ẩn nó đi. 
                # Hiện tại DB chưa có field 'TrangThai' cho TuyenXe, ta báo lỗi cho người dùng.
                messages.error(request, f"Không thể xóa tuyến '{tuyen_xe.tenTuyen}' vì đang có chuyến xe khai thác.")
                # Nếu dùng ajax: return JsonResponse({'status': 'error', 'message': 'Đang có chuyến xe...'})
            else:
                ten = tuyen_xe.tenTuyen
                tuyen_xe.delete()
                messages.success(request, f"Đã xóa tuyến '{ten}' thành công.")

        except Exception as e:
             messages.error(request, f"Có lỗi xảy ra: {e}")

    return redirect('quanlytuyenxe')