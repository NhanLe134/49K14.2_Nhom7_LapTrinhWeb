from nhaxe.models import ChuyenXe, TuyenXe, Nhaxe

print("--- DEBUG TRIPS ---")
try:
    all_trips = ChuyenXe.objects.all()
    print(f"Total trips in DB: {all_trips.count()}")
    for c in all_trips:
        route = c.TuyenXe
        house_id = route.nhaXe_id if route else "NO_ROUTE"
        print(f"TRIP ID: {c.ChuyenXeID} | Route: {route} | House: {house_id}")
except Exception as e:
    print(f"TRIPS ERROR: {e}")

print("\n--- DEBUG HOUSES ---")
try:
    all_houses = Nhaxe.objects.all()
    for h in all_houses:
        # Check field names
        print(f"HOUSE: {h.NhaxeID}")
except Exception as e:
    print(f"HOUSES ERROR: {e}")

print("\n--- DEBUG ROUTES ---")
try:
    all_routes = TuyenXe.objects.all()
    for r in all_routes:
        print(f"ROUTE: {r.tuyenXeID} | House: {r.nhaXe_id}")
except Exception as e:
    print(f"ROUTES ERROR: {e}")
