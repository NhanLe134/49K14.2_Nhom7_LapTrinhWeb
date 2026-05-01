import sys

file_path = r'd:\PycharmProjects\49K14.2_Nhom7_LapTrinhWeb\nhaxe\templates\home\timkiem.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find the seat-view section
seat_view_marker = '<div id="seat-view"'
start_index = content.find(seat_view_marker)

if start_index != -1:
    # Look for the second occurrence of times-row (the first one is in search-view)
    times_row_marker = '<div class="form-row times-row"'
    first_occ = content.find(times_row_marker)
    second_occ = content.find(times_row_marker, first_occ + 1)
    
    if second_occ != -1:
        # Find the gap between the two form-groups in this times-row
        target_gap = '</div>\n                    <div class="form-group">'
        # We need to find this gap WITHIN the second_occ block
        search_from = second_occ
        gap_index = content.find(target_gap, search_from)
        
        if gap_index != -1:
            insertion = '</div>\n                    <div style="width: 150px; flex-shrink: 0;"></div>\n                    <div class="form-group">'
            new_content = content[:gap_index] + insertion + content[gap_index + len(target_gap):]
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print("Successfully updated the file.")
        else:
            print("Gap not found.")
    else:
        print("Second times-row not found.")
else:
    print("seat-view not found.")
