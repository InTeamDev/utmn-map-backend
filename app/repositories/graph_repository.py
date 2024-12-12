# app/repositories/graph_repository.py

import json
import sys
from typing import List

import networkx as nx
from pydantic import ValidationError

from app.domain.models import DataModel, GraphData


class GraphRepository:
    def __init__(self, data_file_path: str):
        self.data_file_path = data_file_path
        self.data = self.load_data()
        self.graph = self.build_graph(self.data.graph)

    def load_data(self) -> DataModel:
        try:
            with open(self.data_file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            validated_data = DataModel(**data)
            return validated_data
        except FileNotFoundError:
            print(f"Файл '{self.data_file_path}' не найден.")
            sys.exit(1)
        except json.JSONDecodeError:
            print(f"Ошибка при разборе JSON файла '{self.data_file_path}'.")
            sys.exit(1)
        except ValidationError as e:
            print(f"Ошибка в структуре данных JSON:\n{e}")
            sys.exit(1)

    def build_graph(self, graph_data: GraphData) -> nx.Graph:
        G = nx.Graph()
        G.add_nodes_from(graph_data.nodes)
        for edge in graph_data.edges:
            from_node = edge['from']
            to_node = edge['to']
            line_id = edge.get('line_id')
            weight = edge.get('weight', 1)
            G.add_edge(from_node, to_node, line_id=line_id, weight=weight)
        return G

    def get_all_object_ids(self) -> List[str]:
        return [obj.id for obj in self.data.objects]

    def get_doors_by_office_id(self, office_id: str) -> List[str]:
        for office in self.data.objects:
            if office.id == office_id:
                return [door.id for door in office.doors]
        return []
