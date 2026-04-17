from django.db import connection
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nhom7.settings')
django.setup()

def get_columns(table_name):
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table_name}'")
        return [row[0] for row in cursor.fetchall()]

print("--- nhaxe_taixe ---")
print(get_columns('nhaxe_taixe'))
print("\n--- nhaxe_user_authentication ---")
print(get_columns('nhaxe_user_authentication'))
