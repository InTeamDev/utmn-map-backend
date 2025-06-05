#!/usr/bin/env python3
import argparse
import math
import re
import sys
import uuid
import xml.etree.ElementTree as ET
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

# ---------------------- Pydantic-модели ----------------------


class ObjectType(BaseModel):
    id: int
    name: str
    alias: str


class Intersection(BaseModel):
    id: UUID
    x: float
    y: float


class Connection(BaseModel):
    from_id: UUID
    to_id: UUID
    weight: float = Field(..., ge=0)
    # type: str  # "door" или "intersection"


class PolygonPoint(BaseModel):
    order: int
    polygon_id: UUID
    x: float
    y: float


class Polygon(BaseModel):
    id: UUID
    label: str  # по умолчанию: "floor"
    z_index: int = 0
    floor_id: UUID
    points: List[PolygonPoint]


class Door(BaseModel):
    id: UUID
    x: float
    y: float
    width: float
    height: float
    object_id: UUID  # ссылка на объект (ObjectModel id)


class ObjectModel(BaseModel):
    id: UUID
    name: str
    alias: str
    description: Optional[str] = None
    x: float
    y: float
    width: float
    height: float
    object_type_id: int


class Floor(BaseModel):
    id: UUID
    name: str
    alias: str
    building_id: UUID
    objects: List[ObjectModel] = []
    doors: List[Door] = []
    polygons: List[Polygon] = []
    intersections: List[Intersection] = []
    connections: List[Connection] = []


class Building(BaseModel):
    id: UUID
    name: str
    address: str
    floors: List[Floor] = []


class CampusSchema(BaseModel):
    object_types: List[ObjectType]
    buildings: List[Building]


# ---------------------- Вспомогательные функции ----------------------


def rects_intersect(x1: float, y1: float, w1: float, h1: float, x2: float, y2: float, w2: float, h2: float) -> bool:
    """
    Проверяет, пересекаются ли два оси-параллельных прямоугольника.
    """
    return not (x2 >= x1 + w1 or x2 + w2 <= x1 or y2 >= y1 + h1 or y2 + h2 <= y1)


def find_matching_point(
    x: float, y: float, doors: dict[UUID, Door], intersections: dict[UUID, Intersection], threshold: float = 10.0
) -> UUID | None:
    """
    Находит ближайшую «точку» (сначала среди intersections, затем среди doors),
    расстояние до которой меньше threshold. Возвращает её UUID, либо None.
    """
    closest_id: UUID | None = None
    min_dist = threshold

    # Сначала проверяем пересечения
    for iid, point in intersections.items():
        dist = math.hypot(point.x - x, point.y - y)
        if dist < min_dist:
            closest_id = iid
            min_dist = dist

    # Если пересечений нет в зоне — проверяем двери
    if closest_id is None:
        for did, door in doors.items():
            cx = door.x + door.width / 2.0
            cy = door.y + door.height / 2.0
            dist = math.hypot(cx - x, cy - y)
            if dist < min_dist:
                closest_id = did
                min_dist = dist

    return closest_id


def parse_id(item_id: str) -> dict[str, str]:
    """
    Разбирает строку вида 'Floor_First_Office_12' → {
      'floor': 'Floor_First',
      'type':  'Office',
      'detail': '12'
    }
    Или 'Floor_Second_Stairs_3' → { 'floor':'Floor_Second', 'type':'Stairs', 'detail':'3' }.
    """
    parts = item_id.split('_')
    result: dict[str, str] = {}
    if len(parts) >= 2:
        result['floor'] = parts[0] + "_" + parts[1]
    if len(parts) >= 3:
        result['type'] = parts[2]
    if len(parts) >= 4:
        result['detail'] = "_".join(parts[3:])
    return result


# ---------------------- Основной парсер одного этажа ----------------------


def parse_svg_floor(
    svg_root: ET.Element, floor_tag: str, floor_uuid: UUID, threshold: float
) -> tuple[
    List[ObjectModel], List[Polygon], dict[UUID, Door], dict[UUID, Intersection], List[Connection], dict[str, UUID]
]:
    """
    Парсит один этаж внутри уже загруженного SVG-дерева:
      1) Объекты      — группа id="{floor_tag}_Offices"
      2) Полигоны     — группа id="{floor_tag}_Background"
      3) Двери        — группа id="{floor_tag}_Doors"
      4) Пересечения  — группа id="{floor_tag}_Intersections"
      5) Линии        — группа id="{floor_tag}_AllowedLines"

    Возвращает:
      objects_list:   [ ObjectModel, … ]
      polygons_list:  [ Polygon, … ]
      doors:          { door_uuid: Door, … }
      intersections:  { inter_uuid: Intersection, … }
      connections:    [ Connection, … ]
      svg_door_map:   { svg_door_id: door_uuid, … }  # для лестниц
    """
    ns = {'svg': 'http://www.w3.org/2000/svg'}

    objects_list: List[ObjectModel] = []
    polygons_list: List[Polygon] = []
    doors: dict[UUID, Door] = {}
    intersections: dict[UUID, Intersection] = {}
    connections: List[Connection] = []
    svg_door_map: dict[str, UUID] = {}

    # --- 1) Парсим объекты (Offices) ---
    group_objs = svg_root.find(f'.//svg:g[@id="{floor_tag}_Offices"]', ns)
    if group_objs is not None:
        for rect in group_objs.findall('svg:rect', ns):
            svg_obj_id = rect.get('id', '')
            if not svg_obj_id:
                continue
            parsed = parse_id(svg_obj_id)
            x = float(rect.get('x', '0'))
            y = float(rect.get('y', '0'))
            w = float(rect.get('width', '0'))
            h = float(rect.get('height', '0'))
            obj_uuid = uuid.uuid4()

            detail = parsed.get('detail', '')
            if detail.isdigit():
                obj_type_id = 1  # cabinet
            elif detail.lower() == 'wardrobe':
                obj_type_id = 6  # wardrobe
            else:
                obj_type_id = 1  # default to cabinet

            obj = ObjectModel(
                id=obj_uuid,
                name=svg_obj_id,
                alias=detail or svg_obj_id,
                description=None,
                x=x,
                y=y,
                width=w,
                height=h,
                object_type_id=obj_type_id,
            )
            objects_list.append(obj)

    # --- 2) Парсим полигоны (Background) ---
    group_bg = svg_root.find(f'.//svg:g[@id="{floor_tag}_Background"]', ns)
    if group_bg is not None:
        # 2.a) Тег <polygon>
        for poly in group_bg.findall('svg:polygon', ns):
            pts = poly.get('points', '').strip()
            if not pts:
                continue
            # Разбиваем строку на числа по пробелам:
            coords_str = pts.split()
            # Преобразуем их в float:
            coords_floats: List[float] = []
            for s in coords_str:
                try:
                    coords_floats.append(float(s))
                except ValueError:
                    continue
            # Должно получиться чётное количество чисел:
            if len(coords_floats) % 2 != 0:
                continue
            # Склеиваем в пары (x, y):
            coords: List[tuple[float, float]] = []
            for i in range(0, len(coords_floats), 2):
                coords.append((coords_floats[i], coords_floats[i + 1]))
            if not coords:
                continue
            poly_uuid = uuid.uuid4()
            points_list: List[PolygonPoint] = []
            for idx, (x_val, y_val) in enumerate(coords, start=1):
                points_list.append(PolygonPoint(order=idx, polygon_id=poly_uuid, x=x_val, y=y_val))
            polygons_list.append(
                Polygon(id=poly_uuid, label='floor', z_index=0, floor_id=floor_uuid, points=points_list)
            )

        # 2.b) Тег <path> — извлекаем все x,y из атрибута d
        for path in group_bg.findall('svg:path', ns):
            d_attr = path.get('d', '')
            raw_pairs = re.findall(r'(-?\d+\.?\d*),(-?\d+\.?\d*)', d_attr)
            if not raw_pairs:
                continue
            coords: List[tuple[float, float]] = []
            for x_str, y_str in raw_pairs:
                try:
                    coords.append((float(x_str), float(y_str)))
                except ValueError:
                    continue
            if not coords:
                continue
            poly_uuid = uuid.uuid4()
            points_list: List[PolygonPoint] = []
            for idx, (x_val, y_val) in enumerate(coords, start=1):
                points_list.append(PolygonPoint(order=idx, polygon_id=poly_uuid, x=x_val, y=y_val))
            polygons_list.append(
                Polygon(id=poly_uuid, label='floor', z_index=0, floor_id=floor_uuid, points=points_list)
            )

    # --- 3) Парсим двери (Doors) и определяем object_id по пересечению с объектом ---
    group_doors = svg_root.find(f'.//svg:g[@id="{floor_tag}_Doors"]', ns)
    if group_doors is not None:
        for rect in group_doors.findall('svg:rect', ns):
            svg_door_id = rect.get('id')
            if not svg_door_id:
                continue
            x = float(rect.get('x', '0'))
            y = float(rect.get('y', '0'))
            w = float(rect.get('width', '0'))
            h = float(rect.get('height', '0'))
            door_uuid = uuid.uuid4()

            # По умолчанию object_id — нулевой UUID, если не найдено пересечений
            assigned_object_id: UUID = UUID(int=0)

            # Находим первый объект, пересекающийся с этой дверью
            for obj in objects_list:
                if rects_intersect(x, y, w, h, obj.x, obj.y, obj.width, obj.height):
                    assigned_object_id = obj.id
                    break
            if assigned_object_id != UUID(int=0):
                door = Door(id=door_uuid, x=x, y=y, width=w, height=h, object_id=assigned_object_id)
                doors[door_uuid] = door
                svg_door_map[svg_door_id] = door_uuid
            else:
                print(f"Предупреждение: дверь '{svg_door_id}' не пересекается ни с одним объектом.", file=sys.stderr)

    # --- 4) Парсим пересечения (Intersections) ---
    group_inters = svg_root.find(f'.//svg:g[@id="{floor_tag}_Intersections"]', ns)
    if group_inters is not None:
        for elem in group_inters:
            new_uuid = uuid.uuid4()
            if elem.tag.endswith('circle'):
                cx = float(elem.get('cx', '0'))
                cy = float(elem.get('cy', '0'))
                intersections[new_uuid] = Intersection(id=new_uuid, x=cx, y=cy)
            elif elem.tag.endswith('rect'):
                x = float(elem.get('x', '0'))
                y = float(elem.get('y', '0'))
                w = float(elem.get('width', '0'))
                h = float(elem.get('height', '0'))
                cx = x + w / 2.0
                cy = y + h / 2.0
                intersections[new_uuid] = Intersection(id=new_uuid, x=cx, y=cy)

    # --- 5) Парсим «разрешённые линии» (AllowedLines) ---
    group_lines = svg_root.find(f'.//svg:g[@id="{floor_tag}_AllowedLines"]', ns)
    if group_lines is not None:
        for line in group_lines.findall('svg:line', ns):
            x1 = float(line.get('x1', '0'))
            y1 = float(line.get('y1', '0'))
            x2 = float(line.get('x2', '0'))
            y2 = float(line.get('y2', '0'))
            p1 = find_matching_point(x1, y1, doors, intersections, threshold)
            p2 = find_matching_point(x2, y2, doors, intersections, threshold)
            if p1 and p2:
                w = math.hypot(x2 - x1, y2 - y1)
                # Определяем тип: если хотя бы один из узлов — дверь, ставим "door"; иначе "intersection"
                # conn_type = "door" if (p1 in doors or p2 in doors) else "intersection"
                connections.append(Connection(from_id=p1, to_id=p2, weight=w))

    return objects_list, polygons_list, doors, intersections, connections, svg_door_map


# ---------------------- Основная логика ----------------------


def main():
    parser = argparse.ArgumentParser(description="Парсит SVG-план и сохраняет результат в JSON через Pydantic-модели.")
    parser.add_argument('-i', '--input', required=True, help="Путь к SVG-файлу.")
    parser.add_argument(
        '-f',
        '--floors',
        nargs='*',
        help="Теги этажей в SVG (например: Floor_First Floor_Second). "
        "Если не указаны, будут определены автоматически.",
    )
    parser.add_argument(
        '-t',
        '--threshold',
        type=float,
        default=10.0,
        help="Порог (в тех же единицах, что и SVG) для поиска совпадений.",
    )
    parser.add_argument('-o', '--output', default='campus_schema.json', help="Файл для сохранения JSON.")
    args = parser.parse_args()

    svg_path = args.input
    threshold = args.threshold
    output_path = args.output

    # Попробуем открыть и распарсить SVG-дерево заранее
    try:
        tree = ET.parse(svg_path)
        svg_root = tree.getroot()
    except ET.ParseError as e:
        print(f"Ошибка при разборе SVG: {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print(f"SVG‐файл '{svg_path}' не найден.", file=sys.stderr)
        sys.exit(1)

    # --------------- Определяем список этажей ---------------
    if args.floors and len(args.floors) > 0:
        floor_tags = args.floors
    else:
        ns = {'svg': 'http://www.w3.org/2000/svg'}
        all_floor_tags: set[str] = set()
        for g in svg_root.findall('.//svg:g', ns):
            gid = g.get('id', '')
            parts = gid.split('_')
            if len(parts) >= 2:
                candidate = parts[0] + "_" + parts[1]
                all_floor_tags.add(candidate)
        floor_tags = sorted(all_floor_tags)

    if not floor_tags:
        print("Не удалось определить ни одного тега этажа.", file=sys.stderr)
        sys.exit(1)

    # --------------- Информация о корпусе (задаётся вручную) ---------------
    BUILDING_ID = uuid.uuid4()
    BUILDING_NAME = "УЛК-05"  # Замените на своё
    BUILDING_ADDRESS = "ул. Перекопская, 15а"  # Замените на своё

    # --------------- Справочник object_types (жёстко заданный) ---------------
    object_types = [
        ObjectType(id=1, name='cabinet', alias='Аудитория'),
        ObjectType(id=2, name='department', alias='Кафедра'),
        ObjectType(id=3, name='man-toilet', alias='Мужской туалет'),
        ObjectType(id=4, name='woman-toilet', alias='Женский туалет'),
        ObjectType(id=5, name='stair', alias='Лестница'),
        ObjectType(id=6, name='wardrobe', alias='Гардероб'),
        ObjectType(id=7, name='gym', alias='Спортзал'),
        ObjectType(id=8, name='cafe', alias='Кафе'),
        ObjectType(id=9, name='canteen', alias='Столовая'),
        ObjectType(id=10, name='chill-zone', alias='Зона отдыха'),
    ]

    # --------------- Сборка данных по этажам ---------------
    floors_models: List[Floor] = []
    stairs_map: dict[str, List[UUID]] = {}  # для межэтажных связей по лестницам

    for floor_tag in floor_tags:
        floor_uuid = uuid.uuid4()
        objs, polys, doors_dict, inters_dict, conns, svg_to_uuid = parse_svg_floor(
            svg_root, floor_tag, floor_uuid, threshold
        )

        # Преобразуем в списки моделей
        objects_list = objs.copy()
        polygons_list = polys.copy()
        doors_list = list(doors_dict.values())
        inters_list = list(inters_dict.values())
        conns_list = conns.copy()

        # Заполняем stairs_map (если дверь типа Stairs)
        for svg_door_id, door_uuid in svg_to_uuid.items():
            parsed = parse_id(svg_door_id)
            if parsed.get('type') == 'Stairs':
                stair_num = parsed.get('detail', '')
                if stair_num:
                    stairs_map.setdefault(stair_num, []).append(door_uuid)

        # Формируем модель этажа
        floor_model = Floor(
            id=floor_uuid,
            name=floor_tag,
            alias=floor_tag,
            building_id=BUILDING_ID,
            objects=objects_list,
            doors=doors_list,
            polygons=polygons_list,
            intersections=inters_list,
            connections=conns_list,
        )
        floors_models.append(floor_model)

    # --------------- Межэтажные связи по лестницам ---------------
    for stair_num, door_uuids in stairs_map.items():
        n = len(door_uuids)
        for i in range(n - 1):
            for j in range(i + 1, n):
                # Поскольку это связь между дверями, тип = "door"
                conn = Connection(from_id=door_uuids[i], to_id=door_uuids[j], weight=threshold * 2.0, type="door")
                floors_models[0].connections.append(conn)

    # --------------- Сборка здания и кампуса ---------------
    building = Building(id=BUILDING_ID, name=BUILDING_NAME, address=BUILDING_ADDRESS, floors=floors_models)

    campus = CampusSchema(object_types=object_types, buildings=[building])

    # --------------- Сохранение в JSON ---------------
    try:
        with open(output_path, 'w', encoding='utf-8') as fout:
            fout.write(campus.model_dump_json(indent=4))
        print(f"JSON сохранён в '{output_path}'.")
    except IOError as e:
        print(f"Ошибка при сохранении JSON: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
