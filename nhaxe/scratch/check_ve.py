import os
import django
import sys

sys.path.append(r'd:\PycharmProjects\49K14.2_Nhom7_LapTrinhWeb')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nhom7.settings')
django.setup()

from nhaxe.models import Ve

ve_list = Ve.objects.all()
print(f"Total tickets: {ve_list.count()}")
for v in ve_list:
    kh_id = v.KhachHang_id if hasattr(v, 'KhachHang_id') else 'N/A'
    cx_id = v.ChuyenXe_id if hasattr(v, 'ChuyenXe_id') else 'N/A'
    print(f"VeID: {v.VeID}, KhachHang: {kh_id}, TrangThai: {v.TrangThai.encode('utf-8', 'ignore')}, ChuyenXe: {cx_id}")
