# app/api/routes.py

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.core.config import settings
from app.repositories.graph_repository import GraphRepository
from app.services.route_service import RouteService
import xml.etree.ElementTree as ET
import os
from tempfile import NamedTemporaryFile

router = APIRouter()


# Зависимости
def get_repository() -> GraphRepository:
    return GraphRepository(data_file_path=settings.data_file_path)


def get_route_service(repository: GraphRepository = Depends(get_repository)) -> RouteService:
    return RouteService(repository)


# Pydantic модели для ответов
class RouteResponse(BaseModel):
    path: List[str]
    line_ids: List[str]
    total_weight: float


@router.get("/floor-plan/{floor}", response_class=FileResponse, summary="Получение SVG плана конкретного этажа")
async def get_floor_plan_by_floor(floor: str):
    """
    Возвращает SVG файл с планом конкретного этажа.
    
    Args:
        floor: Название этажа (например, 'Floor_First', 'Floor_Second', etc.)
    """    
    file_path = "media/улк-5.svg"
    
    # Список всех возможных этажей (в порядке снизу вверх)
    all_floors = ['Floor_First', 'Floor_Second', 'Floor_Third', 'Floor_Fourth']
    
    # Проверяем валидность запрошенного этажа
    if floor not in all_floors:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid floor. Must be one of: {', '.join(all_floors)}"
        )
    
    try:
        # Парсим SVG файл
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        # Получаем индекс текущего этажа
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
                    # Затемняем этажи ниже (чем ниже этаж, тем более прозрачный)
                    opacity = 0.3 + (floor_index / current_floor_index) * 0.2
                    floor_group.set('style', f'opacity:{opacity:.2f}')
                else:
                    # Текущий этаж показываем полностью
                    if 'style' in floor_group.attrib:
                        floor_group.attrib['style'] = floor_group.attrib['style'].replace('display:none', '')
                    floor_group.set('style', floor_group.attrib.get('style', '') + ';opacity:1')
        
        # Создаем временный файл
        with NamedTemporaryFile(delete=False, suffix='.svg') as tmp_file:
            tree.write(tmp_file.name, encoding='utf-8', xml_declaration=True)
            
            async def cleanup_file():
                try:
                    os.unlink(tmp_file.name)
                except Exception:
                    pass
            
            return FileResponse(
                tmp_file.name,
                media_type="image/svg+xml",
                filename=f"улк-5_{floor}.svg",
                background=cleanup_file
            )
            
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="SVG file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/objects", response_model=List[str])
def get_all_objects(repository: GraphRepository = Depends(get_repository)):
    """
    Получение ID всех объектов для поиска.
    """
    return repository.get_all_object_ids()


@router.get("/route", response_model=List[RouteResponse])
def build_route(
    office_a_id: str = Query(..., description="ID кабинета A"),
    office_b_id: str = Query(..., description="ID кабинета B"),
    top_k: int = Query(3, ge=1, description="Количество топ маршрутов"),
    service: RouteService = Depends(get_route_service),
):
    """
    Построение маршрута от кабинета A до кабинета B.
    """
    try:
        routes = service.find_top_k_paths(office_a_id, office_b_id, top_k)
        return routes
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
