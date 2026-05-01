import os
import sys
import django

sys.path.append('C:/Users/Administrator/PycharmProjects/PythonProject/49K14.2_Nhom7_LapTrinhWeb')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nhom7.settings')
django.setup()

from django.db import connection

with connection.cursor() as cursor:
    cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='nhaxe_chuyenxe';")
    columns = [row[0] for row in cursor.fetchall()]
    print("COLUMNS for nhaxe_chuyenxe:", columns)

with connection.cursor() as cursor:
    cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='nhaxe_ghengoi';")
    columns = [row[0] for row in cursor.fetchall()]
    print("COLUMNS for nhaxe_ghengoi:", columns)
