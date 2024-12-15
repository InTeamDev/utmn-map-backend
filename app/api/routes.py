# app/api/routes.py

from typing import List, Dict

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.core.config import settings
from app.repositories.graph_repository import GraphRepository
from app.services.route_service import RouteService
import xml.etree.ElementTree as ET
import os
from tempfile import NamedTemporaryFile
from app.services.svg_processor import process_floor_svg, process_route_svg, add_room_labels
from app.services.object_processor import get_objects_map

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


@router.get("/floor-plan", response_class=FileResponse)
async def get_floor_plan(
    floor: str = Query(..., description="Этаж для отображения"),
    office_a_id: str | None = Query(None, description="ID кабинета A"),
    office_b_id: str | None = Query(None, description="ID кабинета B"),
    top_k: int = Query(1, ge=1, description="Количество топ маршрутов"),
    service: RouteService = Depends(get_route_service),
):
    """
    Возвращает SVG файл с планом этажа. Если указаны office_a_id и office_b_id,
    то также отображает маршрут между ними.
    """
    file_path = "media/улк-5.svg"
    all_floors = ['Floor_First', 'Floor_Second', 'Floor_Third', 'Floor_Fourth']
    
    # Проверяем валидность запрошенного этажа
    if floor not in all_floors:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid floor. Must be one of: {', '.join(all_floors)}"
        )
    
    try:
        tree = ET.parse(file_path)
        
        # Process the SVG based on whether we're showing a route or just a floor
        if office_a_id and office_b_id:
            try:
                routes = service.find_top_k_paths(office_a_id, office_b_id, top_k)
                if not routes:
                    raise HTTPException(status_code=404, detail="No routes found")
                
                route_lines = {}
                for line_id in routes[0]["line_ids"]:
                    line_floor = '_'.join(line_id.split('_')[:2])
                    if line_floor not in route_lines:
                        route_lines[line_floor] = []
                    route_lines[line_floor].append(line_id)
                
                # Add labels before processing the route
                add_room_labels(tree)
                
                if floor not in route_lines:
                    processed_tree = process_floor_svg(tree, floor, all_floors)
                else:
                    processed_tree = process_route_svg(tree, route_lines, all_floors, floor)
                    
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
        else:
            # Add labels before processing the floor
            add_room_labels(tree)
            processed_tree = process_floor_svg(tree, floor, all_floors)
        
        # Создаем временный файл
        with NamedTemporaryFile(delete=False, suffix='.svg') as tmp_file:
            processed_tree.write(tmp_file.name, encoding='utf-8', xml_declaration=True)
            
            async def cleanup_file():
                try:
                    os.unlink(tmp_file.name)
                except Exception:
                    pass
            
            return FileResponse(
                tmp_file.name,
                media_type="image/svg+xml",
                filename=f"floor_{floor}.svg",
                background=cleanup_file
            )
            
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="SVG file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@router.get("/objects", response_model=Dict[str, str])
async def get_objects():
    """
    Возвращает мапу соответствия ID объектов и их человекочитаемых назв��ний.
    """
    file_path = "media/улк-5.svg"
    all_floors = ['Floor_First', 'Floor_Second', 'Floor_Third', 'Floor_Fourth']
    
    try:
        tree = ET.parse(file_path)
        return get_objects_map(tree, all_floors)
            
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="SVG file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))