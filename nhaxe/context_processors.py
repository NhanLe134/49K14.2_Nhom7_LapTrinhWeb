from datetime import datetime
from .models import ChuyenXe

def notifications(request):
    """
    Cung cấp dữ liệu thông báo toàn cục cho template.
    Đếm số lượng chuyến xe đã qua ngày chạy nhưng chưa hoàn thành.
    """
    context = {'overdue_trips_count': 0, 'overdue_trips': []}
    
    # Chỉ xử lý khi đã đăng nhập
    user_id = request.session.get('user_id')
    role = request.session.get('role', '')
    
    # Ở đây kiểm tra role chứa 'nhaxe' hoặc 'nx' (dựa theo logic trong auth_views.py)
    if user_id and role in ['nhaxe', 'nx', 'admin']:
        today = datetime.now().date()
        
        try:
            # Lọc chuyến xe của nhà xe này: 
            # 1. Ngày khởi hành < hôm nay (đã qua ngày chạy)
            # 2. Trạng thái khác 'Hoàn thành' (hoặc là Null)
            overdue_query = ChuyenXe.objects.filter(
                TuyenXe__nhaXe_id=user_id,
                NgayKhoiHanh__lt=today
            ).exclude(TrangThai='Hoàn thành').order_by('-NgayKhoiHanh')
            
            context['overdue_trips_count'] = overdue_query.count()
            # Lấy tối đa 5 chuyến xe trễ nhất để hiện lên popup
            context['overdue_trips'] = overdue_query[:5]
        except Exception:
            pass # Nếu lỗi DB thì mặc định là 0 để không chết toàn trang
            
    return context
