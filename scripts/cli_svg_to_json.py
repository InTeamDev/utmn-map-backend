import argparse
import json
import math
import sys
import xml.etree.ElementTree as ET

import matplotlib.patches as patches
import matplotlib.pyplot as plt


def find_matching_point(x, y, doors, intersections, threshold=10.0):
    closest_point = None
    closest_distance = threshold

    # Сначала проверяем пересечения (приоритет)
    for point_id, point_info in intersections.items():
        px = point_info['position']['x']
        py = point_info['position']['y']
        distance = math.hypot(px - x, py - y)

        if distance < closest_distance:
            closest_point = point_id
            closest_distance = distance

    # Проверяем двери, если пересечение не найдено
    if closest_point is None:
        for point_id, point_info in doors.items():
            # Рассчитываем центр двери
            px = point_info['position']['x'] + point_info['position']['width'] / 2
            py = point_info['position']['y'] + point_info['position']['height'] / 2
            distance = math.hypot(px - x, py - y)

            if distance < closest_distance:
                closest_point = point_id
                closest_distance = distance

    return closest_point


def parse_id(item_id):
    parts = item_id.split('_')
    parsed = {}

    if len(parts) >= 3:
        parsed['floor'] = parts[1]  # Этаж
        parsed['type'] = parts[2]  # Тип объекта (Stairs, Office, Door и т.д.)
        if len(parts) > 3:
            parsed['detail'] = '_'.join(parts[3:])  # Дополнительная информация

    return parsed


def parse_svg(svg_file, floor, threshold):
    # Парсинг SVG
    try:
        tree = ET.parse(svg_file)
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"Ошибка при парсинге SVG-файла: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"SVG-файл '{svg_file}' не найден.")
        sys.exit(1)

    # Пространство имён SVG
    namespaces = {'svg': 'http://www.w3.org/2000/svg'}

    # Словари для хранения информации
    objects = {f"{floor}_Stairs": [], f"{floor}_Offices": []}
    doors_dict = {}  # Словарь дверей для графа
    intersections = {}  # Пересечения

    # Извлечение информации о лестницах
    stairs_group = root.find(f'.//svg:g[@id="{floor}_Stairs"]', namespaces)
    if stairs_group is not None:
        for stair in stairs_group.findall('svg:g', namespaces):
            stair_id = stair.get('id')
            if stair_id:
                parsed_id = parse_id(stair_id)
                objects[f"{floor}_Stairs"].append(
                    {'id': stair_id, 'parsed_id': parsed_id, 'doors': []}  # Инициализация списка дверей
                )
    else:
        print(f"Группа '{floor}_Stairs' не найдена в SVG.")

    # Извлечение информации об офисах
    offices_group = root.find(f'.//svg:g[@id="{floor}_Offices"]', namespaces)
    if offices_group is not None:
        for office in offices_group.findall('svg:rect', namespaces):
            office_id = office.get('id')
            if office_id:
                parsed_id = parse_id(office_id)
                x = float(office.get('x', '0'))
                y = float(office.get('y', '0'))
                width = float(office.get('width', '0'))
                height = float(office.get('height', '0'))
                objects[f"{floor}_Offices"].append(
                    {
                        'id': office_id,
                        'parsed_id': parsed_id,
                        'position': {'x': x, 'y': y, 'width': width, 'height': height},
                        'doors': [],  # Инициализация списка дверей
                    }
                )
    else:
        print(f"Группа '{floor}_Offices' не найдена в SVG.")

    # Извлечение информации о дверях и их ассоциация с объектами
    doors_group = root.find(f'.//svg:g[@id="{floor}_Doors"]', namespaces)
    if doors_group is not None:
        for door in doors_group.findall('svg:rect', namespaces):
            door_id = door.get('id')
            if door_id:
                parsed_id = parse_id(door_id)
                x = float(door.get('x', '0'))
                y = float(door.get('y', '0'))
                width = float(door.get('width', '0'))
                height = float(door.get('height', '0'))

                # Определение объекта, к которому принадлежит дверь
                object_detail = parsed_id.get('detail', '')
                if object_detail.startswith('Office'):
                    object_id = f"{floor}_Office_{object_detail.split('_')[1]}"
                    # Поиск соответствующего офиса
                    for office in objects[f"{floor}_Offices"]:
                        if office['id'] == object_id:
                            door_info = {
                                'id': door_id,
                                'position': {'x': x, 'y': y, 'width': width, 'height': height},
                                'parsed_id': parsed_id,
                            }
                            office['doors'].append(door_info)
                            doors_dict[door_id] = door_info  # Добавление в словарь дверей для графа
                            break
                elif object_detail.startswith('Stairs'):
                    object_id = f"{floor}_Stairs_{object_detail.split('_')[1]}"
                    # Поиск соответствующей лестницы
                    for stair in objects[f"{floor}_Stairs"]:
                        if stair['id'] == object_id:
                            door_info = {
                                'id': door_id,
                                'position': {'x': x, 'y': y, 'width': width, 'height': height},
                                'parsed_id': parsed_id,
                            }
                            stair['doors'].append(door_info)
                            doors_dict[door_id] = door_info  # Добавление в словарь дверей для графа
                            break
                else:
                    print(f"WARN: Дверь '{door_id}' не соответствует известным объектам. Объект: '{object_detail}'")
    else:
        print(f"Группа '{floor}_Doors' не найдена в SVG.")

    # Извлечение информации о пересечениях
    intersections_group = root.find(f'.//svg:g[@id="{floor}_Intersections"]', namespaces)
    if intersections_group is not None:
        for elem in intersections_group:
            elem_id = elem.get('id')
            if elem_id:
                parsed_id = parse_id(elem_id)
                if elem.tag.endswith('circle'):
                    cx = float(elem.get('cx', '0'))
                    cy = float(elem.get('cy', '0'))
                    intersections[elem_id] = {
                        'position': {'x': cx, 'y': cy, 'width': 0, 'height': 0},
                        'parsed_id': parsed_id,
                    }
                elif elem.tag.endswith('rect'):
                    x = float(elem.get('x', '0'))
                    y = float(elem.get('y', '0'))
                    width = float(elem.get('width', '0'))
                    height = float(elem.get('height', '0'))
                    intersections[elem_id] = {
                        'position': {'x': x, 'y': y, 'width': width, 'height': height},
                        'parsed_id': parsed_id,
                    }
    else:
        print(f"Группа '{floor}_Intersections' не найдена в SVG.")

    # Извлечение информации о разрешённых линиях перемещения
    allowed_lines_group = root.find(f'.//svg:g[@id="{floor}_AllowedLines"]', namespaces)
    allowed_lines = []
    if allowed_lines_group is not None:
        for line in allowed_lines_group.findall('svg:line', namespaces):
            line_id = line.get('id')
            x1 = float(line.get('x1', '0'))
            y1 = float(line.get('y1', '0'))
            x2 = float(line.get('x2', '0'))
            y2 = float(line.get('y2', '0'))
            allowed_lines.append({'id': line_id, 'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2})
    else:
        print(f"Группа '{floor}_AllowedLines' не найдена в SVG.")

    # Проверка, что все объекты были успешно распознаны
    num_stairs = len(objects[f"{floor}_Stairs"])
    num_offices = len(objects[f"{floor}_Offices"])
    num_doors = len(doors_dict)
    print(f"Этаж '{floor}': Обнаружено {num_stairs} лестниц, {num_offices} офисов, {num_doors} дверей.")

    # Проверка, что пересечения были успешно распознаны
    print(f"Этаж '{floor}': Обнаружено {len(intersections)} пересечений.")

    # Извлечение узлов графа (двери и пересечения)
    graph_nodes = list(doors_dict.keys()) + list(intersections.keys())

    # Извлечение соединений из разрешённых линий
    graph_edges = []

    for line in allowed_lines:
        line_id = line['id']
        x1 = line['x1']
        y1 = line['y1']
        x2 = line['x2']
        y2 = line['y2']

        point1_id = find_matching_point(x1, y1, doors_dict, intersections, threshold)
        point2_id = find_matching_point(x2, y2, doors_dict, intersections, threshold)

        if point1_id and point2_id:
            graph_edges.append(
                {'from': point1_id, 'to': point2_id, 'line_id': line_id, 'weight': math.hypot(x2 - x1, y2 - y1)}
            )
        else:
            print(f"Предупреждение: Линия '{line_id}' не сопоставлена с дверьми или пересечениями на этаже '{floor}'.")

    graph = {'nodes': graph_nodes, 'edges': graph_edges}

    # Компиляция окончательного JSON
    floor_plan = {
        'floor': floor,
        'objects': objects,
        'doors': doors_dict,  # Добавляем двери
        'intersections': intersections,
        'graph': graph,
    }

    return floor_plan


def save_json(data, output_file):
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"JSON представление успешно создано и сохранено в '{output_file}'")
    except IOError as e:
        print(f"Ошибка при сохранении JSON-файла: {e}")
        sys.exit(1)


def visualize_threshold(all_floor_plans, threshold):
    fig, ax = plt.subplots(figsize=(10, 10))

    door_centers_all = {}
    intersection_centers_all = {}

    # Смещение этажей по оси Y для визуализации
    floor_offset = 0
    floor_spacing = 1000  # Примерное смещение между этажами

    for floor_plan in all_floor_plans:
        floor = floor_plan['floor']
        print(f"Визуализация этажа: {floor}")

        # Смещение координат для этажей
        current_offset = floor_offset
        floor_offset += floor_spacing

        # Парсинг SVG для визуализации объектов
        # Предполагается, что каждая плоскость имеет свои координаты

        # Нарисуем двери
        for door_id, door_info in floor_plan['doors'].items():
            x = door_info['position']['x']
            y = door_info['position']['y'] + current_offset  # Смещение по Y
            width = door_info['position']['width']
            height = door_info['position']['height']
            rect = patches.Rectangle((x, y), width, height, linewidth=1, edgecolor='blue', facecolor='none')
            ax.add_patch(rect)
            # Центр двери
            center_x = x + width / 2
            center_y = y + height / 2
            door_centers_all[f"{floor}_{door_id}"] = (center_x, center_y)
            ax.plot(center_x, center_y, 'bo')  # Синий маркер для двери
            # Круг вокруг двери
            circle = patches.Circle(
                (center_x, center_y), threshold, linewidth=1, edgecolor='blue', facecolor='none', linestyle='--'
            )
            ax.add_patch(circle)

        # Нарисуем пересечения
        for intersection_id, intersection_info in floor_plan['intersections'].items():
            pos = intersection_info['position']
            if 'cx' in intersection_info['parsed_id']:
                cx = pos['x']
                cy = pos['y'] + current_offset
            else:
                x = pos['x']
                y = pos['y'] + current_offset
                cx = x + pos['width'] / 2
                cy = y + pos['height'] / 2
            intersection_centers_all[f"{floor}_{intersection_id}"] = (cx, cy)
            ax.plot(cx, cy, 'ro')  # Красный маркер для пересечения
            # Круг вокруг пересечения
            circle = patches.Circle((cx, cy), threshold, linewidth=1, edgecolor='red', facecolor='none', linestyle='--')
            ax.add_patch(circle)

    # Объединение графов этажей
    combined_nodes = {}
    combined_edges = []

    # Добавление всех узлов и ребер
    for floor_plan in all_floor_plans:
        floor = floor_plan['floor']
        graph = floor_plan['graph']
        for node in graph['nodes']:
            combined_nodes[f"{floor}_{node}"] = {
                'x': door_centers_all.get(f"{floor}_{node}", intersection_centers_all.get(f"{floor}_{node}", (0, 0)))[
                    0
                ],
                'y': door_centers_all.get(f"{floor}_{node}", intersection_centers_all.get(f"{floor}_{node}", (0, 0)))[
                    1
                ],
            }
        for edge in graph['edges']:
            combined_edges.append(
                {
                    'from': f"{floor}_{edge['from']}",
                    'to': f"{floor}_{edge['to']}",
                    'line_id': edge['line_id'],
                    'weight': edge['weight'],
                }
            )

    # Соединение лестниц между этажами
    # Предполагается, что лестницы имеют одинаковые номера на разных этажах
    # Например: Stairs_First, Stairs_Second и т.д.
    stairs_dict = {}
    for floor_plan in all_floor_plans:
        floor = floor_plan['floor']
        for stair in floor_plan['objects'].get(f"{floor}_Stairs", []):
            stair_number = stair['parsed_id'].get('detail', '')
            if stair_number:
                stairs_dict.setdefault(stair_number, []).append(stair['id'])

    # Создание соединений между лестницами разных этажей
    for stair_number, stair_ids in stairs_dict.items():
        sorted_stairs = sorted(
            stair_ids, key=lambda sid: all_floor_plans.index(next(fp for fp in all_floor_plans if fp['floor'] in sid))
        )
        for i in range(len(sorted_stairs) - 1):
            from_floor = next(fp for fp in all_floor_plans if fp['floor'] in sorted_stairs[i])
            to_floor = next(fp for fp in all_floor_plans if fp['floor'] in sorted_stairs[i + 1])
            from_id = f"{from_floor['floor']}_{sorted_stairs[i]}"
            to_id = f"{to_floor['floor']}_{sorted_stairs[i+1]}"
            combined_edges.append(
                {
                    'from': from_id,
                    'to': to_id,
                    'line_id': f"Stairs_{stair_number}_Connection",
                    'weight': threshold * 2,
                }
            )

    # Нарисуем линии и их сопоставленные точки
    for edge in combined_edges:
        from_id = edge['from']
        to_id = edge['to']

        # Получаем координаты точек
        if from_id in combined_nodes:
            x1, y1 = combined_nodes[from_id]['x'], combined_nodes[from_id]['y']
        else:
            print(f"Предупреждение: ID '{from_id}' не найден среди дверей или пересечений.")
            continue

        if to_id in combined_nodes:
            x2, y2 = combined_nodes[to_id]['x'], combined_nodes[to_id]['y']
        else:
            print(f"Предупреждение: ID '{to_id}' не найден среди дверей или пересечений.")
            continue

        ax.plot([x1, x2], [y1, y2], 'g-')  # Зеленые линии
        # Опционально: отображение сопоставленных точек
        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2
        ax.plot(mid_x, mid_y, 'k*')  # Черная звезда для сопоставленной точки

    ax.set_title('Визуализация всех этажей, объединённых через лестницы')
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_aspect('equal', 'box')
    plt.grid(True)
    ax.invert_yaxis()
    plt.show()


def main():
    parser = argparse.ArgumentParser(
        description="Парсер SVG-файлов планов этажей в JSON формат с поддержкой нескольких этажей."
    )
    parser.add_argument('-i', '--input', type=str, required=True, help="Путь к входному SVG-файлу.")
    parser.add_argument(
        '-o', '--output', type=str, default=None, help="Путь к выходному JSON-файлу. По умолчанию 'plan_combined.json'."
    )
    parser.add_argument(
        '-f',
        '--floors',
        type=str,
        nargs='+',
        default=['Floor_First', 'Floor_Second', 'Floor_Third', 'Floor_Fourth'],
        help="Имена этажей, используемые в ID групп SVG. Например: 'Floor_First Floor_Second'.",
    )
    parser.add_argument(
        '-t',
        '--threshold',
        type=float,
        default=10.0,
        help="Пороговое значение для сопоставления точек. По умолчанию 10.0.",
    )
    parser.add_argument(
        '--visualize',
        action='store_true',
        help="Визуализировать порог детектирования.",
    )

    args = parser.parse_args()

    svg_file = args.input
    floors = args.floors
    threshold = args.threshold

    if args.output:
        output_file = args.output
    else:
        output_file = 'plan_combined.json'

    print(f"Парсинг SVG-файла: {svg_file}")
    print(f"Этажи: {', '.join(floors)}")
    print(f"Пороговое значение: {threshold}")
    print(f"Файл вывода: {output_file}")

    all_floor_plans = []
    combined_graph_nodes = set()
    combined_graph_edges = []
    stairs_connections = {  # Словарь для лестниц и связанных с ними дверей
        "First": [],
        "Second": [],
        "Third": [],
        "Fourth": [],
        "Fifth": [],
        "Sixth": [],
    }

    # хранение всех office
    all_objects_list = []
    for floor in floors:
        floor_plan = parse_svg(svg_file, floor, threshold)
        all_floor_plans.append(floor_plan)

        offices = floor_plan['objects'].get(f"{floor}_Offices", [])
        all_objects_list += offices

        # Узлы и рёбра для текущего этажа
        graph = floor_plan['graph']
        combined_graph_nodes.update(graph['nodes'])
        combined_graph_edges.extend(graph['edges'])

        # Сбор дверей, связанных с лестницами
        for stair in floor_plan['objects'].get(f"{floor}_Stairs", []):
            parsed_id = stair.get('parsed_id', {})
            stair_name = parsed_id.get('detail')
            if not stair_name:
                continue
            if stair_name in stairs_connections:
                for door in stair['doors']:
                    stairs_connections[stair_name].append((floor, door['id']))

        print(f"{floor} -> {stairs_connections}")

    # Добавление рёбер между дверями одной лестницы
    for stair_name, doors_by_stair in stairs_connections.items():
        for i in range(len(doors_by_stair) - 1):
            for j in range(i + 1, len(doors_by_stair)):
                floor1, door1 = doors_by_stair[i]
                floor2, door2 = doors_by_stair[j]

                # Найти ID лестницы на этаже floor1, связанной с door1
                stair_id = None
                for stair in all_floor_plans[floors.index(floor1)]['objects'].get(f"{floor1}_Stairs", []):
                    if any(d['id'] == door1 for d in stair['doors']):
                        stair_id = stair['id']
                        break

                combined_graph_edges.append(
                    {
                        'from': f"{door1}",
                        'to': f"{door2}",
                        'line_id': (stair_id if stair_id else f"{stair_name}_Unknown"),
                        'weight': 100,
                    }
                )

    # Сохранение всех этажей в одном JSON
    combined_plan = {
        "objects": all_objects_list,
        # 'floors': all_floor_plans,
        'graph': {
            'nodes': list(combined_graph_nodes),
            'edges': combined_graph_edges,
        },
    }

    save_json(combined_plan, output_file)

    # Визуализация, если флаг установлен
    if args.visualize:
        visualize_threshold(all_floor_plans, threshold)


if __name__ == "__main__":
    main()
