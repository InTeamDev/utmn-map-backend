#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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
    print(f"Обнаружено {num_stairs} лестниц")
    print(f"Обнаружено {num_offices} офисов")
    print(f"Обнаружено {num_doors} дверей")

    # Проверка, что пересечения были успешно распознаны
    print(f"Обнаружено {len(intersections)} пересечений")

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
            print(f"Предупреждение: Линия '{line_id}' не сопоставлена с дверьми или пересечениями.")

    graph = {'nodes': graph_nodes, 'edges': graph_edges}

    # Компиляция окончательного JSON
    floor_plan = {
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


def visualize_threshold(svg_file, floor, threshold, floor_plan):
    fig, ax = plt.subplots(figsize=(10, 10))

    # Парсим SVG для визуализации объектов
    try:
        tree = ET.parse(svg_file)
        root = tree.getroot()
    except Exception as e:
        print(f"Ошибка при парсинге SVG-файла для визуализации: {e}")
        return

    # Пространство имён SVG
    namespaces = {'svg': 'http://www.w3.org/2000/svg'}

    # Нарисуем двери
    doors_group = root.find(f'.//svg:g[@id="{floor}_Doors"]', namespaces)
    door_centers = {}
    if doors_group is not None:
        for door in doors_group.findall('svg:rect', namespaces):
            door_id = door.get('id')
            if door_id in floor_plan['doors']:
                door_info = floor_plan['doors'][door_id]
                x = door_info['position']['x']
                y = door_info['position']['y']
                width = door_info['position']['width']
                height = door_info['position']['height']
                rect = patches.Rectangle((x, y), width, height, linewidth=1, edgecolor='blue', facecolor='none')
                ax.add_patch(rect)
                # Центр двери
                center_x = x + width / 2
                center_y = y + height / 2
                door_centers[door_id] = (center_x, center_y)
                ax.plot(center_x, center_y, 'bo')  # Синий маркер для двери
                # Круг вокруг двери
                circle = patches.Circle(
                    (center_x, center_y), threshold, linewidth=1, edgecolor='blue', facecolor='none', linestyle='--'
                )
                ax.add_patch(circle)
            else:
                print(f"Предупреждение: Дверь '{door_id}' не сопоставлена с пересечениями.")

    # Нарисуем пересечения
    intersections_group = root.find(f'.//svg:g[@id="{floor}_Intersections"]', namespaces)
    intersection_centers = {}
    if intersections_group is not None:
        for elem in intersections_group:
            elem_id = elem.get('id')
            if elem_id in floor_plan['intersections']:
                pos = floor_plan['intersections'][elem_id]['position']
                if elem.tag.endswith('circle'):
                    cx = pos['x']
                    cy = pos['y']
                    intersection_centers[elem_id] = (cx, cy)
                    ax.plot(cx, cy, 'ro')  # Красный маркер для пересечения
                    # Круг вокруг пересечения
                    circle = patches.Circle(
                        (cx, cy), threshold, linewidth=1, edgecolor='red', facecolor='none', linestyle='--'
                    )
                    ax.add_patch(circle)
                elif elem.tag.endswith('rect'):
                    x = pos['x']
                    y = pos['y']
                    width = pos['width']
                    height = pos['height']
                    center_x = x + width / 2
                    center_y = y + height / 2
                    intersection_centers[elem_id] = (center_x, center_y)
                    ax.plot(center_x, center_y, 'ro')  # Красный маркер для пересечения
                    # Круг вокруг пересечения
                    circle = patches.Circle(
                        (center_x, center_y), threshold, linewidth=1, edgecolor='red', facecolor='none', linestyle='--'
                    )
                    ax.add_patch(circle)

    # Нарисуем линии и их сопоставленные точки
    for edge in floor_plan['graph']['edges']:
        from_id = edge['from']
        to_id = edge['to']

        # Получаем координаты точек
        if from_id in door_centers:
            x1, y1 = door_centers[from_id]
        elif from_id in intersection_centers:
            x1, y1 = intersection_centers[from_id]
        else:
            print(f"Предупреждение: ID '{from_id}' не найден среди дверей или пересечений.")
            continue  # Пропустить, если ID не найден

        if to_id in door_centers:
            x2, y2 = door_centers[to_id]
        elif to_id in intersection_centers:
            x2, y2 = intersection_centers[to_id]
        else:
            print(f"Предупреждение: ID '{to_id}' не найден среди дверей или пересечений.")
            continue  # Пропустить, если ID не найден

        ax.plot([x1, x2], [y1, y2], 'g-')  # Зеленые линии
        # Опционально: отображение сопоставленных точек
        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2
        ax.plot(mid_x, mid_y, 'k*')  # Черная звезда для сопоставленной точки

    ax.set_title('Визуализация порога детектирования дверей и пересечений')
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_aspect('equal', 'box')
    plt.grid(True)
    plt.show()


def main():
    parser = argparse.ArgumentParser(description="Парсер SVG-файлов планов этажей в JSON формат.")
    parser.add_argument('-i', '--input', type=str, required=True, help="Путь к входному SVG-файлу.")
    parser.add_argument(
        '-o', '--output', type=str, default=None, help="Путь к выходному JSON-файлу. По умолчанию 'plan_<FLOOR>.json'."
    )
    parser.add_argument(
        '-f',
        '--floor',
        type=str,
        default='Floor_Fourth',
        help="Имя этажа, используемое в ID групп SVG. По умолчанию 'Floor_Fourth'.",
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
    floor = args.floor
    threshold = args.threshold

    if args.output:
        output_file = args.output
    else:
        output_file = f'plan_{floor}.json'

    print(f"Парсинг SVG-файла: {svg_file}")
    print(f"Этаж: {floor}")
    print(f"Пороговое значение: {threshold}")
    print(f"Файл вывода: {output_file}")

    floor_plan = parse_svg(svg_file, floor, threshold)
    save_json(floor_plan, output_file)

    # Визуализация, если флаг установлен
    if args.visualize:
        visualize_threshold(svg_file, floor, threshold, floor_plan)


if __name__ == "__main__":
    main()
