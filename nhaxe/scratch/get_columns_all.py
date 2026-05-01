import os
import sys
import django

sys.path.append('C:/Users/Administrator/PycharmProjects/PythonProject/49K14.2_Nhom7_LapTrinhWeb')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nhom7.settings')
django.setup()

from django.db import connection

with connection.cursor() as cursor:
    cursor.execute("SELECT table_name, column_name FROM information_schema.columns WHERE table_schema='public' ORDER BY table_name, ordinal_position;")
    columns = cursor.fetchall()
    
    current_table = None
    for table, col in columns:
        if table != current_table:
            if current_table is not None:
                print()
            print(f"Table: {table}")
            current_table = table
        print(f"  - {col}")
