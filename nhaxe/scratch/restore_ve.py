import os
import django
import sys

sys.path.append(r'd:\PycharmProjects\49K14.2_Nhom7_LapTrinhWeb')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nhom7.settings')
django.setup()

from nhaxe.models import Ve

updated = Ve.objects.filter(TrangThai='Đã đi').exclude(ChuyenXe__TrangThai='Hoàn thành').update(TrangThai='Đã đặt')
print(f"Restored {updated} tickets back to 'Đã đặt'")
