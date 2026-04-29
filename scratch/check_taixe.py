import os
import django
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.append(".")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nhom7.settings')
django.setup()

from nhaxe.models import Taixe

def check_taixe(id):
    t = Taixe.objects.filter(TaixeID=id).first()
    if t:
        print(f"Taixe found: ID={t.TaixeID}, HoTen='{t.HoTen}', HinhAnhURL='{t.HinhAnhURL}'")
    else:
        print(f"Taixe with ID {id} NOT found.")

if __name__ == "__main__":
    check_taixe("TX00001")
