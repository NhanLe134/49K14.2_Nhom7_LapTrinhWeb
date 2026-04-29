import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nhom7.settings")
django.setup()

from django.db import connection

with connection.cursor() as cursor:
    try:
        cursor.execute('ALTER TABLE "nhaxe_taixe" ALTER COLUMN "HinhAnhURL" TYPE text;')
        print("Column HinhAnhURL changed to type TEXT successfully.")
    except Exception as e:
        print(f"Error altering column: {e}")
