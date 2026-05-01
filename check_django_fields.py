import os
import django
from django.apps import apps

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nhom7.settings')
django.setup()

Nhaxe = apps.get_model('nhaxe', 'Nhaxe')
fields = [f.name for f in Nhaxe._meta.get_fields()]
print(f"Django sees these fields for Nhaxe: {fields}")
