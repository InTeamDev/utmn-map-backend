from typing import Any, Dict, List

from pydantic import BaseModel


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
