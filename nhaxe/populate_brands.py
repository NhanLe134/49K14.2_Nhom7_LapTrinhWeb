import os
import django
from decimal import Decimal

# Setup Django if running as a standalone script
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nhom7.settings')
django.setup()


def populate_brands():
    # Targets for 16-30 seats
    brands_data = [
        {'brand': 'Ford Transit', 'seats': 16, 'price': 200000},
        {'brand': 'Hyundai Solati', 'seats': 16, 'price': 220000},
        {'brand': 'Thaco Town', 'seats': 29, 'price': 280000},
        {'brand': 'Isuzu Samco', 'seats': 29, 'price': 270000},
        {'brand': 'Samco Felix', 'seats': 30, 'price': 300000},
    ]
    
    # We need a Nhaxe to link these brands to via CHITIETLOAIXE
    # We found NX00001 in the DB earlier
    nha_xe = Nhaxe.objects.filter(NhaxeID='NX00001').first()
    if not nha_xe:
        print("Nhaxe NX00001 not found. Please log in first or create a Nhaxe record.")
        return

    for item in brands_data:
        # 1. Create the base Loaixe (Type)
        # Note: We can have multiple Loaixe for the same seat count to distinguish brands if needed,
        # but the current model design is a bit ambiguous if Loaixe is "category" or "specific model".
        # I'll create one Loaixe per brand configuration choice to be safe.
        lx = Loaixe.objects.create(
            SoCho=item['seats'],
            GiaVe=Decimal(str(item['price']))
        )
        
        # 2. Link to Nhaxe via CHITIETLOAIXE with the brand name
        CHITIETLOAIXE.objects.get_or_create(
            Nhaxe=nha_xe,
            Loaixe=lx,
            defaults={'TenLoaiXe': item['brand'], 'Tennhaxe': nha_xe.NhaxeID}
        )
        print(f"Created {item['brand']} (ID: {lx.LoaixeID}, {item['seats']} seats)")

if __name__ == '__main__':
    populate_brands()
