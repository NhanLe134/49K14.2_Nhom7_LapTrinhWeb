import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nhom7.settings')
django.setup()

from nhaxe.models import User_Authentication, Taixe

def check_user(username):
    print(f"Checking user: {username}")
    user = User_Authentication.objects.filter(TenDangNhap=username).first()
    if not user:
        print("User not found.")
        return
    
    print(f"User ID: {user.UserID}")
    print(f"Role: {user.Vaitro}")
    print(f"Linked Taixe: {user.Taixe}")
    
    if user.Taixe:
        print(f"Taixe ID: {user.Taixe.TaixeID}")
        print(f"Taixe HoTen: '{user.Taixe.HoTen}'")
        print(f"Taixe HinhAnhURL: {user.Taixe.HinhAnhURL}")
    else:
        print("This user is NOT linked to any Taixe record.")

if __name__ == "__main__":
    check_user("TX1")
