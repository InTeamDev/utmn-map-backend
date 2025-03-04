from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import routes

app = FastAPI(
    title="Маршрутизация Кабинетов API",
    description="API для получения списка объектов и построения маршрутов между кабинетами.",
    version="1.0.0",
)



app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes.router)
