from django.shortcuts import redirect
from functools import wraps

def yeu_cau_nha_xe(ham_view):
    """Decorator yêu cầu quyền Nhà xe hoặc Admin để truy cập."""
    @wraps(ham_view)
    def thuc_thi(request, *args, **kwargs):
        ma_nguoi_dung = request.session.get('user_id')
        vai_tro = (request.session.get('role') or '').lower()
        
        # Chấp nhận các biến thể của vai trò Nhà xe
        cac_vai_tro_hop_le = ['nhaxe', 'nx', 'admin', 'nhà xe', 'nha xe']
        if ma_nguoi_dung and any(vt in vai_tro for vt in cac_vai_tro_hop_le):
            return ham_view(request, *args, **kwargs)
        
        return redirect('/dangnhap?next=' + request.path)
    return thuc_thi

def yeu_cau_tai_xe(ham_view):
    """Decorator yêu cầu quyền Tài xế để truy cập."""
    @wraps(ham_view)
    def thuc_thi(request, *args, **kwargs):
        ma_nguoi_dung = request.session.get('user_id')
        vai_tro = (request.session.get('role') or '').lower()
        
        cac_vai_tro_hop_le = ['taixe', 'tx', 'driver', 'tài xế', 'tai xe']
        if ma_nguoi_dung and any(vt in vai_tro for vt in cac_vai_tro_hop_le):
            return ham_view(request, *args, **kwargs)
            
        return redirect('/dangnhap?next=' + request.path)
    return thuc_thi

def yeu_cau_khach_hang(ham_view):
    """Decorator yêu cầu quyền Khách hàng để truy cập."""
    @wraps(ham_view)
    def thuc_thi(request, *args, **kwargs):
        ma_nguoi_dung = request.session.get('user_id')
        vai_tro = (request.session.get('role') or '').lower()
        
        cac_vai_tro_hop_le = ['khach', 'khách', 'kh', 'customer']
        if ma_nguoi_dung and any(vt in vai_tro for vt in cac_vai_tro_hop_le):
            return ham_view(request, *args, **kwargs)
            
        return redirect('/dangnhap?next=' + request.path)
    return thuc_thi
