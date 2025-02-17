## Скрипты в папке scripts:

1. `scripts/cli_assign_door_ids.py` - для автоматического присвоения id дверям. Работает на основе ID office и ID stairs
2. `scripts/cli_svg_to_json.py` - для конвертации svg в json, нужен для получения данных для визуализации
3. `scripts/cli_find.py` - cli версия построения маршрута

## установка

```
python -m venv .venv

source .venv/bin/activate

pip install -r requirements.txt

uvicorn app.main:app --reload
```

Чтобы закрыть venv, нужно прописать deactivate или просто закрыть терминал

дока - http://localhost:8000/docs

## запуск в докере

`docker-compose up --build`
