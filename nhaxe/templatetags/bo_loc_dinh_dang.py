from django import template

register = template.Library()

@register.filter
def vnd(gia_tri):
    """
    Chuyển đổi con số thành định dạng tiền tệ Việt Nam (phân cách nghìn bằng dấu chấm)
    Ví dụ: 110000 -> 110.000
    """
    try:
        # Chuyển về số nguyên để bỏ phần thập phân
        gia_tri_so = int(float(gia_tri))
        # Định dạng có dấu phẩy rồi đổi phẩy thành chấm
        return "{:,}".format(gia_tri_so).replace(',', '.')
    except (ValueError, TypeError):
        return gia_tri
