import os
import sys
import django

sys.path.append('C:/Users/Administrator/PycharmProjects/PythonProject/49K14.2_Nhom7_LapTrinhWeb')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nhom7.settings')
django.setup()

from django.db import connection

tables = ['nhaxe_loaixe', 'nhaxe_tuyenxe', 'nhaxe_chuyenxe']
for table in tables:
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name='{table}';")
        columns = [row[0] for row in cursor.fetchall()]
        print(f"COLUMNS for {table}:", columns)
