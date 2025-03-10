import json
import math
from typing import Optional

from app.domain.user_context import Location, UserContext
from app.services.cache import SearchCache
from app.utils.ranker import PopularityRanker
from app.utils.text_processing import (
    advanced_normalize_text_with_stemming,
    calculate_relevance,
    expand_synonyms,
    fuzzy_match,
    handle_translit,
    handle_typos,
)


def load_data(filepath: str):
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)["objects"]


# Основная функция поиска
def search_entities(query: str, user_floor: str, user_context: Optional[UserContext], data: list[dict]):
    # Инициализация компонентов
    cache = SearchCache()
    popularity_ranker = PopularityRanker()

    # Проверка кэша
    cache_key = f"{query}:{user_floor}"
    if user_context:
        cache_key += f":{user_context.time}:{user_context.location.x}:{user_context.location.y}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result

        # Обработка запроса
        query = advanced_normalize_text_with_stemming(handle_translit(query))
        query = handle_typos(query)
        query = expand_synonyms(query, 'data/synonyms.json')

        results = []
        for obj in data:
            obj_type = obj["parsed_id"]["type"].lower()
            obj_detail = obj["parsed_id"]["detail"].lower()
            obj_floor = obj["parsed_id"]["floor"].lower()

            if fuzzy_match(query, obj_type) or fuzzy_match(query, obj_detail):
                if user_floor.lower() == obj_floor:
                    relevance = calculate_relevance(query, obj, user_context)
                    popularity = popularity_ranker.get_popularity_score(obj["id"])

                    if relevance > 0.5:
                        result = {
                            "id": obj["id"],
                            "relevance": relevance,
                            "popularity": popularity,
                            "floor": obj["parsed_id"]["floor"],
                            "type": obj["parsed_id"]["type"],
                            "detail": obj["parsed_id"]["detail"],
                            "position": obj["position"],
                        }

                        if user_context and user_context.location:
                            distance = calculate_distance(user_context.location, obj["position"])
                            result["distance"] = distance

                        results.append(result)

        # Сортировка с учетом всех факторов
        results.sort(
            key=lambda x: (
                x["floor"] != user_floor if user_floor else False,
                -x["relevance"],
                -x["popularity"],
                x.get("distance", float('inf')) if user_context and user_context.location else 0,
            )
        )

        # Кэширование результата
        cache.set(cache_key, results)

        return results


def calculate_distance(location1: Location, location2: dict) -> float:
    """
    Рассчитывает нормализованное расстояние между двумя точками.

    Параметры:
    - location1: словарь с координатами {"x": float, "y": float}
    - location2: словарь с координатами {"x": float, "y": float}

    Возвращает:
    float: нормализованное значение расстояния от 0 до 1 (где 1 - ближайшее расположение)
    """
    try:
        # Евклидово расстояние
        dx = location1.x - location2["x"]
        dy = location1.y - location2["y"]
        distance = math.sqrt(dx * dx + dy * dy)

        # Нормализация расстояния
        # Предполагаем, что максимальное расстояние в здании = 100 единиц
        MAX_DISTANCE = 100.0

        # Преобразуем расстояние в оценку релевантности (1 - близко, 0 - далеко)
        relevance = 1 - min(distance / MAX_DISTANCE, 1)

        return max(0.1, relevance)  # Минимальная релевантность 0.1

    except (KeyError, TypeError):
        return 0.5  # В случае ошибки возвращаем среднее значение
