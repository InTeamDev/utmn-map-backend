from typing import Dict
import xml.etree.ElementTree as ET
from fastapi import HTTPException

def get_objects_map(svg_tree: ET.ElementTree, all_floors: list[str]) -> Dict[str, str]:
    """
    Создает мапу соответствия ID объектов и их человекочитаемых названий.
    """
    try:
        objects_map = {}
        root = svg_tree.getroot()
        
        # Обрабатываем все группы с id
        for floor_group in root.findall(".//*[@id]"):
            element_id = floor_group.get('id', '')
            
            # Пропускаем служебные группы
            if any(x in element_id for x in ["AllowedLines", "Intersections", "Doors"]):
                continue
                
            # Проверяем принадлежность к этажу
            floor_match = next((f for f in all_floors if element_id.startswith(f)), None)
            if floor_match and len(element_id.split('_')) >= 3:
                parts = element_id.split('_')
                floor_name = parts[1].replace("First", "1").replace("Second", "2") \
                                  .replace("Third", "3").replace("Fourth", "4")
                
                if parts[2] == "Office" and len(parts) > 3:
                    readable_name = f"Кабинет {parts[3]}"
                    objects_map[element_id] = f"{readable_name} ({floor_name} этаж)"
                elif parts[2] == "Stairs" and len(parts) > 3:
                    readable_name = f"Лестница {parts[3]}"
                    objects_map[element_id] = f"{readable_name} ({floor_name} этаж)"
        
        return objects_map
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing SVG: {str(e)}") 