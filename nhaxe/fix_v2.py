import codecs
import re
import os

paths = [
    r'd:\LTW\nhom7\nhaxe\templates\home\khachhang.html', 
    r'd:\LTW\nhom7\nhaxe\templates\home\quanlyve.html', 
    r'd:\LTW\nhom7\nhaxe\templates\home\timkiem.html',
    r'd:\LTW\nhom7\nhaxe\templates\home\danhgiachuyenxe.html',
    r'd:\LTW\nhom7\nhaxe\templates\home\dadanhgia.html',
    r'd:\LTW\nhom7\nhaxe\templates\home\vietdanhgia.html'
]

for p in paths:
    if not os.path.exists(p):
        print(f"Skipping {p} (Not Found)")
        continue
        
    with codecs.open(p, 'r', 'utf-8') as f:
        text = f.read()

    # Add load static if missing
    if "{% load static %}" not in text:
        text = "{% load static %}\n" + text

    # Handle CSS links
    text = re.sub(r'href="[^"]*CSS/CSS/khachhang\.css"', r'href="{% static \'css/khachhang.css\' %}"', text)
    text = re.sub(r'href="[^"]*CSS/CSS/timkiem\.css"', r'href="{% static \'css/timkiem.css\' %}"', text)
    text = re.sub(r'href="quanlyve\.css"', r'href="{% static \'css/quanlyve.css\' %}"', text)
    
    # Handle Image links
    text = re.sub(r'src="[^"]*Vexeapp_logo\.png"', r'src="{% static \'img/Vexeapp_logo.png\' %}"', text)
    text = re.sub(r'src="(QRCODE\.png)"', r'src="{% static \'img/QRCODE.png\' %}"', text)
    
    # Map .html hrefs directly to Django URL tags
    def repl_url(match):
        filename = match.group(1)
        if filename == "vecuatoi":
            filename = "quanlyve"  # Reroute legacy vecuatoi links to quanlyve
        return f'href="{{% url \'{filename}\' %}}"'
    
    text = re.sub(r'href="([a-zA-Z0-9_]+)\.html"', repl_url, text)

    # Hardcoded `#` link fixes for specific templates
    text = text.replace('<a href="#" class="dropdown-item">\n                    <i class="fa-solid fa-gear"></i> Quản lý tài khoản', 
                        '<a href="{% url \'thongtin_khachhang\' %}" class="dropdown-item">\n                    <i class="fa-solid fa-gear"></i> Quản lý tài khoản')
                        
    text = text.replace('<a href="#" class="sidebar-item">\n                <i class="fa-solid fa-comments" style="color: #444;"></i> Đánh giá chuyến xe', 
                        '<a href="{% url \'danhgiachuyenxe\' %}" class="sidebar-item">\n                <i class="fa-solid fa-comments" style="color: #444;"></i> Đánh giá chuyến xe')

    with codecs.open(p, 'w', 'utf-8') as f:
        f.write(text)
        
    print(f"Successfully patched {p}")
