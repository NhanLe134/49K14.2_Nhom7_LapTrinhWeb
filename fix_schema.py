import os
import django
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nhom7.settings')
django.setup()

def add_column_if_not_exists(table_name, column_name, column_def):
    with connection.cursor() as cursor:
        cursor.execute(f"""
            SELECT COUNT(*) 
            FROM information_schema.columns 
            WHERE table_name = '{table_name}' AND column_name = '{column_name}'
        """)
        if cursor.fetchone()[0] == 0:
            print(f"Adding column {column_name} to {table_name}...")
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_def}")
        else:
            print(f"Column {column_name} already exists in {table_name}.")

try:
    # Add HoTenNguoiDaiDien to Nhaxe
    add_column_if_not_exists('nhaxe_nhaxe', 'HoTenNguoiDaiDien', 'VARCHAR(200)')
    
    # Add NgayDangKy to KhachHang (just in case)
    add_column_if_not_exists('nhaxe_khachhang', 'NgayDangKy', 'TIMESTAMP WITH TIME ZONE')
    
    # Add GiaVe and NgayCapNhatGia to chitietloaixe (since 0026 failed here)
    add_column_if_not_exists('nhaxe_chitietloaixe', 'GiaVe', 'DECIMAL(12, 0) DEFAULT 0')
    add_column_if_not_exists('nhaxe_chitietloaixe', 'NgayCapNhatGia', 'DATE')
    
    print("Schema update completed successfully.")
except Exception as e:
    print(f"Error updating schema: {e}")
