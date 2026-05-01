from datetime import datetime
from .models import ChuyenXe, KhachHang, Nhaxe, User_Authentication

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

def user_info(request):
    """
    Cung cấp thông tin tên người dùng toàn cục.
    """
    user_id = request.session.get('user_id')
    user_name = None
    
    if user_id:
        try:
            # Lấy User_Authentication kèm theo các bảng liên quan để tối ưu query
            auth_user = User_Authentication.objects.select_related('KhachHang', 'Nhaxe', 'Taixe').get(UserID=user_id)
            
            if auth_user.KhachHang:
                user_name = auth_user.KhachHang.HovaTen
            elif auth_user.Nhaxe:
                user_name = auth_user.Nhaxe.TenNhaXe
            elif auth_user.Taixe:
                user_name = auth_user.Taixe.HoTen
            
            # Fallback nếu chưa có họ tên thật
            if not user_name:
                user_name = auth_user.TenDangNhap
        except Exception:
            pass
            
    return {'user_name': user_name}
