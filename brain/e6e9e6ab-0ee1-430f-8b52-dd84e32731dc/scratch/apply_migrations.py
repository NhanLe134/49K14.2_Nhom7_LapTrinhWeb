import os
import sys
import django
from django.db import connection

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nhom7.settings')
django.setup()

def run_sql(sql):
    with connection.cursor() as cursor:
        print(f"Executing: {sql}")
        cursor.execute(sql)

try:
    # 1. Add HoTen to nhaxe_taixe
    run_sql('ALTER TABLE nhaxe_taixe ADD COLUMN IF NOT EXISTS "HoTen" VARCHAR(255)')
    
    # 2. Check and ensure nhaxe_user_authentication has needed fields
    # Supabase uses lowercase usually but Django quoted "HoTen" usually means case sensitive.
    # In my experience with Supabase, case sensitivity matters if quoted.
    
    print("Schema updates applied successfully.")
except Exception as e:
    print(f"Error applying schema updates: {e}")
