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