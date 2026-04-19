import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nhom7.settings')
django.setup()

from nhaxe.models import ChuyenXe, CHITIETTAIXE, Taixe, Xe

print("Checking data integrity...")

# Check trips without drivers or cars
broken_trips = ChuyenXe.objects.filter(Taixe__isnull=True)
if broken_trips.exists():
    print(f"Broken trips (no driver): {broken_trips.count()}")

# Check drivers without detail records
drivers = Taixe.objects.all()
for d in drivers:
    if not CHITIETTAIXE.objects.filter(Taixe=d).exists():
        print(f"Driver {d.TaixeID} ({d.HoTen}) has no CHITIETTAIXE record.")

print("Check finished.")
