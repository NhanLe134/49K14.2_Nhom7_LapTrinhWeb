import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nhom7.settings")
django.setup()

from django.db import connection

with connection.cursor() as cursor:
    try:
        cursor.execute('ALTER TABLE "nhaxe_taixe" ADD COLUMN "NgayHetHanBangLai" date NULL;')
        print("Column NgayHetHanBangLai added successfully.")
    except Exception as e:
        print(f"Error: {e}")
