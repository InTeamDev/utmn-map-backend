import json
from heapq import nsmallest

import networkx as nx


def load_data(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data


def get_office_doors(objects, office_id):
    for office in objects:
        if office['id'] == office_id:
            return [door['id'] for door in office.get('doors', [])]
    return []


def build_graph(data):
    G = nx.Graph()

    # Добавляем узлы
    nodes = data.get('nodes', [])
    G.add_nodes_from(nodes)

    # Добавляем ребра с атрибутами
    edges = data.get('edges', [])
    for edge in edges:
        from_node = edge['from']
        to_node = edge['to']
        line_id = edge.get('line_id')
        weight = edge.get('weight', 1)
        G.add_edge(from_node, to_node, line_id=line_id, weight=weight)

    return G


def extract_line_ids(G, path):
    line_ids = []
    for i in range(len(path) - 1):
        edge_data = G.get_edge_data(path[i], path[i + 1])
        if edge_data:
            # Если несколько ребер между узлами, берем первое
            if isinstance(edge_data, dict):
                # Для неориентированного графа edge_data уже содержит оба направления
                line_id = edge_data.get('line_id')
                if isinstance(line_id, list):
                    line_id = line_id[0]
                line_ids.append(line_id)
    return line_ids


def compute_path_weight(G, path):
    total_weight = 0
    for i in range(len(path) - 1):
        edge_data = G.get_edge_data(path[i], path[i + 1])
        if edge_data and 'weight' in edge_data:
            total_weight += edge_data['weight']
        else:
            total_weight += 1  # Значение по умолчанию, если вес не указан
    return total_weight


def main():
    # Путь к вашему JSON файлу
    file_path = 'plan_combined.json'

    # Входные данные: ID кабинета A и кабинета B
    office_a_id = input("Введите ID кабинета A: ").strip()
    office_b_id = input("Введите ID кабинета B: ").strip()

    # Загрузка данных
    data = load_data(file_path)

    # Получение дверей для кабинетов A и B
    doors_a = get_office_doors(data.get('all_objects', {}), office_a_id)
    print(f"Двери кабинета A ({office_a_id}): {doors_a}")
    doors_b = get_office_doors(data.get('all_objects', {}), office_b_id)
    print(f"Двери кабинета B ({office_b_id}): {doors_b}")

    if not doors_a:
        print(f"Кабинет A с ID '{office_a_id}' не найден или у него нет дверей.")
        return
    if not doors_b:
        print(f"Кабинет B с ID '{office_b_id}' не найден или у него нет дверей.")
        return

    # Построение графа
    G = build_graph(data.get('combined_graph', {}))

    top_k = 3  # Количество топ маршрутов
    all_top_paths = []

    for door_a in doors_a:
        for door_b in doors_b:
            if door_a == door_b:
                continue
            try:
                # Генератор путей, отсортированных по общей длине
                paths_generator = nx.shortest_simple_paths(G, source=door_a, target=door_b, weight='weight')

                # Получаем первые top_k путей
                for _ in range(top_k):
                    path = next(paths_generator)
                    total_weight = compute_path_weight(G, path)
                    all_top_paths.append((path, total_weight))
            except (nx.NetworkXNoPath, StopIteration):
                # Нет пути или меньше топ_k путей доступно
                continue

    if not all_top_paths:
        print("Маршруты от кабинета A до кабинета B не найдены.")
        return

    # Выбираем глобальные топ_k маршрутов
    global_top_paths = nsmallest(top_k, all_top_paths, key=lambda x: x[1])

    # Убираем дубликаты путей
    unique_top_paths = []
    seen_paths = set()
    for path, weight in global_top_paths:
        path_tuple = tuple(path)
        if path_tuple not in seen_paths:
            seen_paths.add(path_tuple)
            unique_top_paths.append((path, weight))
        if len(unique_top_paths) == top_k:
            break

    # Извлечение line_id для каждого пути и вывод результатов
    print(f"Топ-{len(unique_top_paths)} самых кратчайших маршрутов от '{office_a_id}' до '{office_b_id}':")
    for idx, (path, weight) in enumerate(unique_top_paths, 1):
        line_ids = extract_line_ids(G, path)
        print(f"\nМаршрут {idx}:")
        print(f"Путь: {' -> '.join(path)}")
        print(f"Линии: {line_ids}")
        print(f"Общая длина: {weight}")


if __name__ == "__main__":
    main()
