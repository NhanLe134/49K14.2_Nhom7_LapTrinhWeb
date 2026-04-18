from django.shortcuts import render
from django.contrib import messages
from django.http import JsonResponse
from .xu_ly_tim_kiem import tim_kiem_chuyen_xe_kha_dung, lay_so_do_ghe

def view_tim_kiem_ve(request):
    """
    Function-based view xử lý tìm kiếm chuyến xe.
    Lấy các tham số origin, destination, depart_date từ phương thức GET.
    """
    origin = request.GET.get('origin', '').strip()
    destination = request.GET.get('destination', '').strip()
    depart_date = request.GET.get('depart_date', '').strip()

    try:
        if origin and destination and depart_date:
            # Gọi hàm từ file xu_ly_tim_kiem.py để lấy danh sách chuyến xe
            danh_sach_chuyen = tim_kiem_chuyen_xe_kha_dung(origin, destination, depart_date)
            
            if not danh_sach_chuyen:
                messages.info(request, "Không tìm thấy chuyến xe nào phù hợp với yêu cầu.")
        else:
            danh_sach_chuyen = []
            # Nếu người dùng đã bấm nút tìm kiếm (ví dụ có tham số search_submitted) nhưng thiếu thông tin
            if request.GET.get('search_submitted'):
                messages.warning(request, "Vui lòng nhập đầy đủ thông tin: Điểm đi, Điểm đến và Ngày đi.")

        # Trả dữ liệu về template timkiem.html
        context = {
            'chuyen_xe_list': danh_sach_chuyen,
            'origin': origin,
            'destination': destination,
            'depart_date': depart_date
        }
        return render(request, 'home/timkiem.html', context)

    except Exception as e:
        # Xử lý ngoại lệ try...except tương tự chuyenxe_views.py
        messages.error(request, f"Lỗi hệ thống khi tìm kiếm: {str(e)}")
        return render(request, 'home/timkiem.html', {
            'chuyen_xe_list': [],
            'origin': origin,
            'destination': destination,
            'depart_date': depart_date
        })

def lay_so_do_ghe_api(request):
    """
    API endpoint trả về sơ đồ ghế của một chuyến xe dưới dạng JSON.
    """
    chuyen_id = request.GET.get('chuyen_id')
    if not chuyen_id:
        return JsonResponse({'status': 'error', 'message': 'Thiếu ID chuyến xe'}, status=400)
    
    try:
        data = lay_so_do_ghe(chuyen_id)
        return JsonResponse({'status': 'success', 'data': data})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
