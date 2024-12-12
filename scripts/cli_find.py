import argparse
import json
import sys
from heapq import nsmallest
from typing import Any, Dict, List

import networkx as nx
from pydantic import BaseModel, ValidationError


class ParsedID(BaseModel):
    floor: str
    type: str
    detail: str


class Position(BaseModel):
    x: float
    y: float
    width: float
    height: float


class Door(BaseModel):
    id: str
    position: Position
    parsed_id: ParsedID


class Object(BaseModel):
    id: str
    parsed_id: ParsedID
    position: Position
    doors: List[Door]


class GraphData(BaseModel):
    nodes: List[str]
    edges: List[Dict[str, Any]]


class DataModel(BaseModel):
    objects: List[Object]
    graph: GraphData


def load_data(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        # Валидация данных через Pydantic
        validated_data = DataModel(**data)
        return validated_data
    except FileNotFoundError:
        print(f"Файл '{file_path}' не найден.")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Ошибка при разборе JSON файла '{file_path}'.")
        sys.exit(1)
    except ValidationError as e:
        print(f"Ошибка в структуре данных JSON:\n{e}")
        sys.exit(1)


def get_office_doors(objects: List[Object], office_id: str) -> List[str]:
    for office in objects:
        if office.id == office_id:
            return [door.id for door in office.doors]
    return []


def build_graph(graph_data: GraphData):
    G = nx.Graph()

    # Добавляем узлы
    nodes = graph_data.nodes
    G.add_nodes_from(nodes)

    # Добавляем ребра с атрибутами
    for edge in graph_data.edges:
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
            total_weight += 1
    return total_weight


def main():
    parser = argparse.ArgumentParser(description="Найти топ-K кратчайших маршрутов между двумя офисами.")
    parser.add_argument('-i', '--input', type=str, help="Путь к JSON файлу с данными (например, plan_combined.json)")
    parser.add_argument('-a', '--office_a_id', type=str, help="ID кабинета A")
    parser.add_argument('-b', '--office_b_id', type=str, help="ID кабинета B")
    parser.add_argument('-k', '--top_k', type=int, default=3, help="Количество топ маршрутов (по умолчанию: 3)")

    args = parser.parse_args()

    if not args.input or not args.office_a_id or not args.office_b_id:
        parser.print_help()
        sys.exit(1)

    file_path = args.input
    office_a_id = args.office_a_id
    office_b_id = args.office_b_id
    top_k = args.top_k

    # Загрузка данных
    data = load_data(file_path)

    # Получение дверей для кабинетов A и B
    doors_a = get_office_doors(data.objects, office_a_id)
    doors_b = get_office_doors(data.objects, office_b_id)

    if not doors_a:
        print(f"Кабинет A с ID '{office_a_id}' не найден или у него нет дверей.")
        sys.exit(1)
    if not doors_b:
        print(f"Кабинет B с ID '{office_b_id}' не найден или у него нет дверей.")
        sys.exit(1)

    # Построение графа
    G = build_graph(data.graph)

    all_top_paths = []

    for door_a in doors_a:
        for door_b in doors_b:
            if door_a == door_b:
                continue
            try:
                paths_generator = nx.shortest_simple_paths(G, source=door_a, target=door_b, weight='weight')
                for _ in range(top_k):
                    path = next(paths_generator)
                    total_weight = compute_path_weight(G, path)
                    all_top_paths.append((path, total_weight))
            except (nx.NetworkXNoPath, StopIteration):
                continue

    if not all_top_paths:
        print("Маршруты от кабинета A до кабинета B не найдены.")
        sys.exit(1)

    global_top_paths = nsmallest(top_k, all_top_paths, key=lambda x: x[1])

    unique_top_paths = []
    seen_paths = set()
    for path, weight in global_top_paths:
        path_tuple = tuple(path)
        if path_tuple not in seen_paths:
            seen_paths.add(path_tuple)
            unique_top_paths.append((path, weight))
        if len(unique_top_paths) == top_k:
            break

    print(f"\nТоп-{len(unique_top_paths)} самых кратчайших маршрутов от '{office_a_id}' до '{office_b_id}':")
    for idx, (path, weight) in enumerate(unique_top_paths, 1):
        line_ids = extract_line_ids(G, path)
        print(f"\nМаршрут {idx}:")
        print(f"Путь: {' -> '.join(path)}")
        print(f"Линии: {line_ids}")
        print(f"Общая длина: {weight}")


if __name__ == "__main__":
    main()
