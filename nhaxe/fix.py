import codecs
paths = [r'd:\LTW\nhom7\nhaxe\templates\home\khachhang.html', 
         r'd:\LTW\nhom7\nhaxe\templates\home\quanlyve.html', 
         r'd:\LTW\nhom7\nhaxe\templates\home\timkiem.html']

for p in paths:
    try:
        with codecs.open(p, 'r', 'utf-8') as f:
            text = f.read()
    except Exception as e:
        print(f"Could not read {p}")
        continue

    if "{% load static %}" not in text:
        text = "{% load static %}\n" + text
        
    replacements = {
        'href="../CSS/CSS/khachhang.css"': 'href="{% static \'css/khachhang.css\' %}"',
        'href="../CSS/CSS/timkiem.css"': 'href="{% static \'css/timkiem.css\' %}"',
        'href="quanlyve.css"': 'href="{% static \'css/quanlyve.css\' %}"',
        'src="../picture/Vexeapp_logo.png"': 'src="{% static \'img/Vexeapp_logo.png\' %}"',
        'src="QRCODE.png"': 'src="{% static \'img/QRCODE.png\' %}"',
        'href="thongtin_khachhang.html"': 'href="{% url \'thongtin_khachhang\' %}"',
        'href="index.html"': 'href="{% url \'index\' %}"',
        'href="khachhang.html"': 'href="{% url \'khachhang\' %}"',
        'href="timkiem.html"': 'href="{% url \'timkiem\' %}"',
        'href="vecuatoi.html"': 'href="{% url \'quanlyve\' %}"',
        'href="quanlyve.html"': 'href="{% url \'quanlyve\' %}"',
        'href="danhgiachuyenxe.html"': 'href="{% url \'danhgiachuyenxe\' %}"',
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
        
    # Special handle for '#' dropdowns to map to correct paths
    text = text.replace('<a href="#" class="dropdown-item">\n                    <i class="fa-solid fa-gear"></i> Quản lý tài khoản', 
                        '<a href="{% url \'thongtin_khachhang\' %}" class="dropdown-item">\n                    <i class="fa-solid fa-gear"></i> Quản lý tài khoản')
                        
    text = text.replace('<a href="#" class="sidebar-item">\n                <i class="fa-solid fa-comments" style="color: #444;"></i> Đánh giá chuyến xe', 
                        '<a href="{% url \'danhgiachuyenxe\' %}" class="sidebar-item">\n                <i class="fa-solid fa-comments" style="color: #444;"></i> Đánh giá chuyến xe')

    with codecs.open(p, 'w', 'utf-8') as f:
        f.write(text)
    
    print(f"Fixed {p}")

print("Done")
