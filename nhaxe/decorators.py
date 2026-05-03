from django.shortcuts import redirect
from functools import wraps

def nhaxe_required(function):
    @wraps(function)
    def wrap(request, *args, **kwargs):
        user_id = request.session.get('user_id')
        role = (request.session.get('role') or '').lower()
        # Chấp nhận cả có dấu và không dấu cho Nhà xe
        if user_id and (role in ['nhaxe', 'nx', 'admin'] or 'nhà xe' in role or 'nha xe' in role):
            return function(request, *args, **kwargs)
        return redirect('/dangnhap?next=' + request.path)
    return wrap

def taixe_required(function):
    @wraps(function)
    def wrap(request, *args, **kwargs):
        user_id = request.session.get('user_id')
        role = (request.session.get('role') or '').lower()
        # Chấp nhận cả có dấu và không dấu cho Tài xế
        if user_id and (role in ['taixe', 'tx', 'driver'] or 'tài xế' in role or 'tai xe' in role):
            return function(request, *args, **kwargs)
        return redirect('/dangnhap?next=' + request.path)
    return wrap

def khachhang_required(function):
    @wraps(function)
    def wrap(request, *args, **kwargs):
        user_id = request.session.get('user_id')
        role = (request.session.get('role') or '').lower()
        # Chấp nhận cả có dấu và không dấu cho Khách hàng
        if user_id and ('khach' in role or 'khách' in role or 'kh' == role or 'customer' in role):
            return function(request, *args, **kwargs)
        return redirect('/dangnhap?next=' + request.path)
    return wrap
