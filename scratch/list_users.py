import os
import django
import sys
import io

# Fix encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.append(".")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nhom7.settings')
django.setup()

from nhaxe.models import User_Authentication

def list_users():
    users = User_Authentication.objects.all()
    print(f"Total users: {len(users)}")
    for u in users:
        try:
            print(f" - ID: {u.UserID}, Username: '{u.TenDangNhap}', Role: {u.Vaitro}, Taixe_id: {u.Taixe_id}")
        except Exception as e:
            print(f" - Error printing user {u.UserID}: {e}")

if __name__ == "__main__":
    list_users()
