import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nhom7.settings')
django.setup()

from nhaxe.templatetags import bo_loc_dinh_dang
print("Import successful")
