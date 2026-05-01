import os
import django
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nhom7.settings')
django.setup()

def list_columns(table_name):
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table_name}'")
        columns = [row[0] for row in cursor.fetchall()]
        print(f"Columns in {table_name}: {columns}")

list_columns('nhaxe_nhaxe')
