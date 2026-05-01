import os
import django
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nhom7.settings')
django.setup()

def fix_column_case(table_name, old_name, new_name):
    with connection.cursor() as cursor:
        print(f"Renaming {old_name} to \"{new_name}\" in {table_name}...")
        cursor.execute(f'ALTER TABLE {table_name} RENAME COLUMN "{old_name}" TO "{new_name}"')

try:
    # Rename lowercase column to CamelCase quoted column
    fix_column_case('nhaxe_nhaxe', 'hotennguoidaidien', 'HoTenNguoiDaiDien')
    print("Column renamed successfully.")
except Exception as e:
    print(f"Error renaming column: {e}")
