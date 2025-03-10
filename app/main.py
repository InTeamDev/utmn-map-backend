import threading
import time

import psutil
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Gauge
from prometheus_fastapi_instrumentator import Instrumentator

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


instrumentator = Instrumentator().instrument(app)

cpu_usage_gauge = Gauge("system_cpu_usage", "CPU Usage Percentage")
memory_usage_gauge = Gauge("system_memory_usage", "Memory Usage Percentage")
disk_usage_gauge = Gauge("system_disk_usage", "Disk Usage Percentage")


def update_system_metrics():
    """Периодически обновляет системные метрики"""
    while True:
        cpu_usage_gauge.set(psutil.cpu_percent(interval=1))
        memory_usage_gauge.set(psutil.virtual_memory().percent)
        disk_usage_gauge.set(psutil.disk_usage('/').percent)
        time.sleep(1)


threading.Thread(target=update_system_metrics, daemon=True).start()

instrumentator.expose(app, endpoint="/metrics")
