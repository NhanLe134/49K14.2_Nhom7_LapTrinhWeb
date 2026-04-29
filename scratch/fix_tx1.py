import os
import django
import sys

sys.path.append(".")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nhom7.settings')
django.setup()

from nhaxe.models import Taixe

def fix_taixe(id, name, avatar=None):
    t = Taixe.objects.filter(TaixeID=id).first()
    if t:
        t.HoTen = name
        if avatar:
            t.HinhAnhURL = avatar
        t.save()
        print(f"Fixed Taixe {id}: Name set to '{name}'")
    else:
        print(f"Taixe {id} not found.")

if __name__ == "__main__":
    # Setting a professional name and a sample avatar for TX1
    fix_taixe("TX00001", "Nguyễn Văn Tài", "https://i.pravatar.cc/150?u=tx1")
