
from rapidfuzz.fuzz import partial_ratio
import json
import re
import math
import nltk
from nltk.tokenize import word_tokenize
from datetime import datetime
from transliterate import translit
from symspellpy import SymSpell
from nltk.tokenize import word_tokenize
from nltk.stem.snowball import SnowballStemmer
from functools import lru_cache

# Инициализация стеммера для русского языка
stemmer = SnowballStemmer("russian")

nltk.download('punkt')



# Настройка SymSpell
sym_spell = SymSpell(max_dictionary_edit_distance=2)
sym_spell.load_dictionary("frequency_dictionary_ru.txt", term_index=0, count_index=1)

# Словарь цифр для обработки чисел
NUMBERS = {
    "один": "1", "два": "2", "три": "3", "четыре": "4", "пять": "5",
    "шесть": "6", "семь": "7", "восемь": "8", "девять": "9", "десять": "10"
}

# Преобразование текста (нормализация)
def normalize_text(text: str) -> str:
    text = text.lower()
    for word, num in NUMBERS.items():
        text = text.replace(word, num)
    return text

# Обработка транслита
def handle_translit(text: str) -> str:
    return translit(text, 'ru', reversed=True)

# Обработка опечаток с SymSpell
def handle_typos(query: str) -> str:
    suggestions = sym_spell.lookup_compound(query, max_edit_distance=2)
    return suggestions[0].term if suggestions else query

# Лемматизация и очистка текста
def advanced_normalize_text_with_stemming(text: str) -> str:
    """
    Нормализация текста с использованием стемминга, удалением пунктуации и стоп-слов.

    Аргументы:
    text (str): Исходный текст.

    Возвращает:
    str: Нормализованный текст.
    """
    # Приведение текста к нижнему регистру
    text = text.lower()

    # Удаление спецсимволов
    text = re.sub(r'[^\w\s]', '', text)

    # Токенизация текста
    tokens = word_tokenize(text)

    # Стемминг
    stemmed_tokens = [stemmer.stem(token) for token in tokens]

    # Удаление стоп-слов
    stop_words = set(['и', 'в', 'во', 'не', 'что', 'он', 'на', 'я', 'с', 'со', 'как'])
    filtered_tokens = [token for token in stemmed_tokens if token not in stop_words]

    # Объединение токенов в строку
    return ' '.join(filtered_tokens)

def load_synonyms(file_path: str) -> dict:
    with open(file_path, "r", encoding="utf-8") as f:
        synonyms = json.load(f)

    # Создаём обратный словарь
    reverse_synonyms = {}
    for key, values in synonyms.items():
        for value in values:
            reverse_synonyms[value] = key  # Привязываем синоним к ключу
    return reverse_synonyms

def expand_synonyms(text: str, synonyms_file: str) -> str:
    # Загружаем обратный словарь
    reverse_synonyms = load_synonyms(synonyms_file)

    # Разбиваем текст на токены
    tokens = text.split()

    # Заменяем токены на основное слово
    expanded_tokens = [reverse_synonyms.get(token, token) for token in tokens]

    # Собираем текст обратно
    return ' '.join(expanded_tokens)

# Нечеткий поиск
def fuzzy_match(query: str, target: str) -> bool:
    return partial_ratio(query, target) > 80 or query in target


def get_time_relevance(obj: dict, user_time: datetime) -> float:
    if "working_hours" not in obj:
        return 1.0

    current_hour = user_time.hour
    try:
        open_hour = int(obj["working_hours"]["open"].split(":")[0])
        close_hour = int(obj["working_hours"]["close"].split(":")[0])

        if open_hour <= current_hour < close_hour:
            middle_hour = (open_hour + close_hour) / 2
            time_diff = abs(current_hour - middle_hour)
            max_diff = (close_hour - open_hour) / 2
            return 1 - (time_diff / max_diff) * 0.5
        else:
            hours_until_open = (open_hour - current_hour) % 24
            return max(0.1, 0.5 - (hours_until_open / 24))
    except (KeyError, ValueError):
        return 1.0

# Расчет расстояния
def calculate_distance(location1: dict, location2: dict) -> float:
    try:
        dx = location1["x"] - location2["x"]
        dy = location1["y"] - location2["y"]
        distance = math.sqrt(dx**2 + dy**2)
        MAX_DISTANCE = 100.0
        relevance = 1 - min(distance / MAX_DISTANCE, 1)
        return max(0.1, relevance)
    except (KeyError, TypeError):
        return 0.5

# Расчет общей релевантности
def calculate_relevance(query, obj, user_context):
    text_similarity = partial_ratio(query, obj["parsed_id"]["detail"]) / 100
    time_relevance = get_time_relevance(obj, user_context.time)
    location_relevance = calculate_distance(user_context.location, obj["position"])

    weights = {"text": 0.5, "time": 0.3, "location": 0.2}
    relevance_score = (
        text_similarity * weights["text"] +
        time_relevance * weights["time"] +
        location_relevance * weights["location"]
    )
    return relevance_score
