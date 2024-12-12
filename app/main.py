from fastapi import FastAPI

from app.api import routes

app = FastAPI(
    title="Маршрутизация Кабинетов API",
    description="API для получения списка объектов и построения маршрутов между кабинетами.",
    version="1.0.0",
)

app.include_router(routes.router)
