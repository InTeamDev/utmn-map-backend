from heapq import nsmallest
from typing import Any, Dict, List, Tuple

import networkx as nx

from app.repositories.graph_repository import GraphRepository


class RouteService:
    def __init__(self, repository: GraphRepository):
        self.repository = repository
        self.G = self.repository.graph

    def extract_line_ids(self, path: List[str]) -> List[Any]:
        line_ids = []
        for i in range(len(path) - 1):
            edge_data = self.G.get_edge_data(path[i], path[i + 1])
            if edge_data:
                line_id = edge_data.get('line_id')
                if isinstance(line_id, list):
                    line_id = line_id[0]
                line_ids.append(line_id)
        return line_ids

    def compute_path_weight(self, path: List[str]) -> float:
        total_weight = 0
        for i in range(len(path) - 1):
            edge_data = self.G.get_edge_data(path[i], path[i + 1])
            if edge_data and 'weight' in edge_data:
                total_weight += edge_data['weight']
            else:
                total_weight += 1
        return total_weight

    def find_top_k_paths(self, office_a_id: str, office_b_id: str, top_k: int = 3) -> List[Dict[str, Any]]:
        doors_a = self.repository.get_doors_by_office_id(office_a_id)
        doors_b = self.repository.get_doors_by_office_id(office_b_id)

        if not doors_a:
            raise ValueError(f"Кабинет A с ID '{office_a_id}' не найден или у него нет дверей.")
        if not doors_b:
            raise ValueError(f"Кабинет B с ID '{office_b_id}' не найден или у него нет дверей.")

        all_top_paths: List[Tuple[List[str], float]] = []

        for door_a in doors_a:
            for door_b in doors_b:
                if door_a == door_b:
                    continue
                try:
                    paths_generator = nx.shortest_simple_paths(self.G, source=door_a, target=door_b, weight='weight')
                    for _ in range(top_k):
                        path = next(paths_generator)
                        total_weight = self.compute_path_weight(path)
                        all_top_paths.append((path, total_weight))
                except (nx.NetworkXNoPath, StopIteration):
                    continue

        if not all_top_paths:
            raise ValueError("Маршруты от кабинета A до кабинета B не найдены.")

        global_top_paths = nsmallest(top_k, all_top_paths, key=lambda x: x[1])

        unique_top_paths = []
        seen_paths = set()
        for path, weight in global_top_paths:
            path_tuple = tuple(path)
            if path_tuple not in seen_paths:
                seen_paths.add(path_tuple)
                unique_top_paths.append({"path": path, "line_ids": self.extract_line_ids(path), "total_weight": weight})
            if len(unique_top_paths) == top_k:
                break

        return unique_top_paths
