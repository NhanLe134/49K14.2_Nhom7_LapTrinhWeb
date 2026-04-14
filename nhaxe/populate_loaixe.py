from nhaxe.models import Loaixe
from decimal import Decimal

def add_default_loaixe():
    data = [
        {'SoCho': 16, 'GiaVe': Decimal('200000')},
        {'SoCho': 29, 'GiaVe': Decimal('250000')},
        {'SoCho': 30, 'GiaVe': Decimal('300000')},
    ]

    for item in data:
        # Check if already exists to avoid duplicates (though IDs are auto-gen)
        if not Loaixe.objects.filter(SoCho=item['SoCho']).exists():
            obj = Loaixe.objects.create(
                SoCho=item['SoCho'],
                GiaVe=item['GiaVe']
            )
            print(f"Added: {obj.LoaixeID} - {item['SoCho']} seats")
        else:
            print(f"Already exists: {item['SoCho']} seats")

if __name__ == '__main__':
    add_default_loaixe()
