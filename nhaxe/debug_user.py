import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nhom7.settings')
django.setup()

from nhaxe.models import User_Authentication, KhachHang

username = "kh1"
user = User_Authentication.objects.filter(TenDangNhap=username).first()

if user:
    print(f"User ID: {user.UserID}")
    print(f"Vaitro in DB: '{user.Vaitro}'")
    print(f"Role processed: '{(user.Vaitro or '').lower()}'")
    print(f"KhachHang Relationship: {user.KhachHang}")
    if user.KhachHang:
        print(f"KhachHang HovaTen: '{user.KhachHang.HovaTen}'")
    
    # Check if 'khach' in role logic
    role = (user.Vaitro or '').lower()
    print(f"Condition ('khach' in role): {'khach' in role}")
    print(f"Condition ('kh' == role): {'kh' == role}")
else:
    print(f"User '{username}' not found.")
