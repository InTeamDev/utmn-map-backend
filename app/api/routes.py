# app/api/routes.py

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.core.config import settings
from app.repositories.graph_repository import GraphRepository
from app.services.route_service import RouteService

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


@router.get("/floor-plan", response_class=FileResponse, summary="Получение SVG плана этажей")
def get_floor_plan():
    """
    Возвращает SVG файл с планом этажей.
    """
    file_path = "media/улк-5.svg"
    try:
        return FileResponse(file_path, media_type="image/svg+xml", filename="улк-5.svg")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Файл не найден")


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
