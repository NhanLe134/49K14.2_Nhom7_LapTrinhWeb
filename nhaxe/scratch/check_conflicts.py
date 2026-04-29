import os
import glob
import sys
sys.stdout.reconfigure(encoding='utf-8')

files = [
    "nhaxe/auth_views.py",
    "nhaxe/models.py",
    "nhaxe/taixe_views.py",
    "nhaxe/templates/home/quanlyve.html",
    "nhaxe/urls.py",
    "nhaxe/views.py",
]

for file_path in files:
    full_path = os.path.join(r'd:\PycharmProjects\49K14.2_Nhom7_LapTrinhWeb', file_path)
    if not os.path.exists(full_path):
        continue
    with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()
    
    in_conflict = False
    conflict_blocks = []
    current_block = []
    
    for i, line in enumerate(lines):
        if line.startswith('<<<<<<< HEAD'):
            in_conflict = True
            current_block.append(f"--- Line {i+1} ---\n{line}")
        elif in_conflict:
            current_block.append(line)
            if line.startswith('>>>>>>>'):
                in_conflict = False
                conflict_blocks.append("".join(current_block))
                current_block = []
                
    if conflict_blocks:
        print(f"\n====================== {file_path} ======================")
        for b in conflict_blocks:
            print(b.encode('utf-8', 'replace').decode('utf-8', 'ignore'))
            print("="*40)
