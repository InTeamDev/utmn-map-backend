import xml.etree.ElementTree as ET
from typing import List

def process_floor_svg(
    svg_tree: ET.ElementTree,
    floor: str,
    all_floors: List[str]
) -> ET.ElementTree:
    """
    Обрабатывает SVG файл для отображения конкретного этажа.
    
    Args:
        svg_tree: Parsed ElementTree SVG файла
        floor: Название этажа
        all_floors: Список всех этажей
    
    Returns:
        ET.ElementTree: Обработанный SVG файл
    """
    root = svg_tree.getroot()
    current_floor_index = all_floors.index(floor)
    
    # Обрабатываем все группы с id
    for floor_group in root.findall(".//*[@id]"):
        floor_id = floor_group.get('id', '')
        
        # Скрываем все линии и точки пересечения
        if "AllowedLines" in floor_id or "Intersections" in floor_id:
            floor_group.set('style', 'display:none')
            continue
        
        # Определяем, к какому этажу относится группа
        floor_match = next((f for f in all_floors if floor_id.startswith(f)), None)
        if floor_match:
            floor_index = all_floors.index(floor_match)
            
            if floor_index > current_floor_index:
                # Скрываем этажи выше
                floor_group.set('style', 'display:none')
            elif floor_index < current_floor_index:
                # Затемняем этажи ниже (более мягкое затемнение)
                opacity = 0.6 + (floor_index / current_floor_index) * 0.3
                floor_group.set('style', f'opacity:{opacity:.2f}')
            else:
                # Текущий этаж показываем полностью
                if 'style' in floor_group.attrib:
                    floor_group.attrib['style'] = floor_group.attrib['style'].replace('display:none', '')
                floor_group.set('style', floor_group.attrib.get('style', '') + ';opacity:1')
    
    return svg_tree 

def process_route_svg(
    svg_tree: ET.ElementTree,
    route_lines: dict[str, List[str]],  # Словарь {этаж: [line_ids]}
    all_floors: List[str],
    requested_floor: str
) -> ET.ElementTree:
    """
    Обрабатывает SVG файл для отображения маршрута.
    """
    root = svg_tree.getroot()
    
    # Используем запрошенный этаж вместо самого нижнего
    current_floor_index = all_floors.index(requested_floor)
    
    # Сначала скроем все линии
    for group in root.findall(".//*[@id]"):
        if "AllowedLines" in group.get('id', ''):
            for element in group:
                element.set('style', 'display:none')
    
    # Обрабатываем все группы с id
    for floor_group in root.findall(".//*[@id]"):
        floor_id = floor_group.get('id', '')
        
        # Обрабатываем группы линий
        if "AllowedLines" in floor_id:
            floor = next((f for f in all_floors if floor_id.startswith(f)), None)
            if floor and floor in route_lines:
                # Показываем только линии маршрута
                for element in floor_group:
                    element_id = element.get('id', '')
                    if element_id in route_lines[floor]:
                        element.set('style', 'stroke:#70B62C;stroke-width:3;display:inline')
                    else:
                        element.set('style', 'stroke:#C9E6FA')
                        
            continue
        
        # Скрываем все точки пересечения
        if "Intersections" in floor_id:
            floor_group.set('style', 'display:none')
            continue
        
        # Определяем, к какому этажу относится группа
        floor_match = next((f for f in all_floors if floor_id.startswith(f)), None)
        if floor_match:
            floor_index = all_floors.index(floor_match)
            
            if floor_index > current_floor_index:
                # Скрываем этажи выше
                floor_group.set('style', 'display:none')
            elif floor_index < current_floor_index:
                # Затемняем этажи ниже
                opacity = 0.6 + (floor_index / current_floor_index) * 0.3
                floor_group.set('style', f'opacity:{opacity:.2f}')
            else:
                # Текущий этаж показываем полностью
                if 'style' in floor_group.attrib:
                    floor_group.attrib['style'] = floor_group.attrib['style'].replace('display:none', '')
                floor_group.set('style', floor_group.attrib.get('style', '') + ';opacity:1')
    
    return svg_tree

def add_room_labels(tree: ET.ElementTree):
    """
    Adds text labels to rooms in the SVG.
    """
    root = tree.getroot()
    ns = {'svg': 'http://www.w3.org/2000/svg'}
    
    # Словарь специальных помещений и их меток
    special_rooms = {
        "Toilet": "Туалет",
        "Gym": "Спортзал",
        "Kitchen": "Кухня",
        "Wardrobe": "Гардероб",
        "Dining": "Столовая",
        "Server": "Серверная"
    }
    
    # Process each floor
    for floor in ['Floor_First', 'Floor_Second', 'Floor_Third', 'Floor_Fourth']:
        # Find offices group
        offices_group = root.find(f".//svg:g[@id='{floor}_Offices']", namespaces=ns)
        if offices_group is None:
            continue
            
        # Create a new group for labels if it doesn't exist
        labels_group = root.find(f".//svg:g[@id='{floor}_Labels']", namespaces=ns)
        if labels_group is None:
            labels_group = ET.SubElement(offices_group, '{http://www.w3.org/2000/svg}g')
            labels_group.set('id', f'{floor}_Labels')
            
        # Process each office rectangle
        for office in offices_group.findall('svg:rect', namespaces=ns):
            office_id = office.get('id', '')
            if not office_id or 'IDK' in office_id:
                continue
                
            # Get office details from ID
            parts = office_id.split('_')
            if len(parts) < 4:
                continue
                
            # Get the room label based on special cases
            label = None
            for room_type, room_label in special_rooms.items():
                if room_type in office_id:
                    label = room_label
                    break
            
            # If no special room type found, use the original ID
            if label is None:
                label = parts[3]
            
            # Calculate text position (center of rectangle)
            try:
                x = float(office.get('x', '0')) + float(office.get('width', '0')) / 2
                y = float(office.get('y', '0')) + float(office.get('height', '0')) / 2
            except (ValueError, TypeError):
                continue
            
            # Check if label already exists
            existing_label = labels_group.find(f".//svg:text[@data-office-id='{office_id}']", namespaces=ns)
            if existing_label is not None:
                continue
                
            # Create text element
            text = ET.SubElement(labels_group, '{http://www.w3.org/2000/svg}text')
            text.set('x', str(x))
            text.set('y', str(y))
            text.set('text-anchor', 'middle')
            text.set('dominant-baseline', 'middle')
            text.set('font-size', '14')
            text.set('fill', '#000000')
            text.set('data-office-id', office_id)
            text.text = label
