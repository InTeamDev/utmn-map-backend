#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import sys
import uuid
import xml.etree.ElementTree as ET


def parse_id(element_id):
    """
    Парсит ID элемента и возвращает словарь с типом и номером объекта.
    Предполагается, что ID имеют формат 'Floor_Second_Office_201' или 'Floor_Second_Stairs_1'.
    """
    parts = element_id.split('_')
    return {'type': parts[2] if len(parts) > 2 else '', 'number': parts[3] if len(parts) > 3 else ''}


def is_overlap_with_threshold(rect1, rect2, threshold=10):
    """
    Проверяет пересечение двух прямоугольников с учетом порога.

    rect1 и rect2 должны быть словарями с ключами 'x', 'y', 'width', 'height'.
    Порог расширяет rect2 на ±threshold пикселей со всех сторон.
    """
    # Расширяем прямоугольник rect2 на порог
    expanded_rect2 = {
        'x': rect2['x'] - threshold,
        'y': rect2['y'] - threshold,
        'width': rect2['width'] + 2 * threshold,
        'height': rect2['height'] + 2 * threshold,
    }
    # Проверка пересечения
    return not (
        rect1['x'] + rect1['width'] < expanded_rect2['x']
        or expanded_rect2['x'] + expanded_rect2['width'] < rect1['x']
        or rect1['y'] + rect1['height'] < expanded_rect2['y']
        or expanded_rect2['y'] + expanded_rect2['height'] < rect1['y']
    )


def remove_namespaces(tree):
    """
    Удаляет пространство имен из всех тегов XML дерева.
    """
    for elem in tree.iter():
        # Убираем пространство имен из тега
        if '}' in elem.tag:
            elem.tag = elem.tag.split('}', 1)[1]


def assign_new_ids_with_threshold(root, doors_group, objects, stairs_group, floor, threshold=10):
    """
    Присваивает дверям новые ID на основе их положения относительно офисов и лестниц с учетом порога.
    Обеспечивает уникальность ID дверей, добавляя суффикс при необходимости.
    """
    # Сбор всех офисов с их позициями
    offices = objects.get(f"{floor}_Offices", [])
    stairs = objects.get(f"{floor}_Stairs", [])

    # Сбор всех дверей
    doors = doors_group.findall('svg:rect', namespaces={'svg': 'http://www.w3.org/2000/svg'})

    # Инициализация счетчиков для офисов и лестниц
    office_door_counters = {}
    stair_door_counters = {}
    unassigned_door_counter = 1  # Счетчик для не назначенных дверей

    for index, door in enumerate(doors, start=1):  # Используем индекс для генерации временного ID
        door_id = door.get('id')
        if not door_id:
            print("Предупреждение: У двери без ID присваивается временный ID.")
            door_id = f"{floor}_Door_Unassigned_{index}"
            door.set('id', door_id)
            continue

        x = float(door.get('x', '0'))
        y = float(door.get('y', '0'))
        width = float(door.get('width', '0'))
        height = float(door.get('height', '0'))
        door_rect = {'x': x, 'y': y, 'width': width, 'height': height}

        # Проверка пересечения с каждым офисом
        assigned = False
        for office in offices:
            office_rect = office['position']
            if is_overlap_with_threshold(door_rect, office_rect, threshold=threshold):
                # Извлекаем уникальную часть ID офиса
                office_number = office['id'].split('_')[-1]
                # Инициализируем счетчик для этого офиса, если еще не инициализирован
                if office['id'] not in office_door_counters:
                    office_door_counters[office['id']] = 1
                else:
                    office_door_counters[office['id']] += 1
                door_suffix = office_door_counters[office['id']]
                new_id = f"{floor}_Door_Office_{office_number}_{door_suffix}"
                print(f"Дверь {door_id} пересекается с офисом {office['id']}; присваивается новый ID: {new_id}")
                door.set('id', new_id)
                assigned = True
                break  # Предполагаем, что дверь может быть связана только с одним объектом

        if not assigned:
            for stair in stairs:
                stair_rect = stair.get('position', {})
                if stair_rect and is_overlap_with_threshold(door_rect, stair_rect, threshold=threshold):
                    stair_number = stair['id'].split('_')[-1]
                    # Инициализируем счетчик для этой лестницы, если еще не инициализирован
                    if stair['id'] not in stair_door_counters:
                        stair_door_counters[stair['id']] = 1
                    else:
                        stair_door_counters[stair['id']] += 1
                    door_suffix = stair_door_counters[stair['id']]
                    new_id = f"{floor}_Door_Stairs_{stair_number}_{door_suffix}"
                    print(f"Дверь {door_id} пересекается с лестницей {stair['id']}; присваивается новый ID: {new_id}")
                    door.set('id', new_id)
                    assigned = True
                    break  # Предполагаем, что дверь может быть связана только с одним объектом

        if not assigned:
            # Если не пересекается ни с одним офисом или лестницей, присваиваем уникальный ID
            new_id = f"{floor}_Door_Unassigned_{unassigned_door_counter}"
            print(f"Дверь {door_id} не пересекается с ни одним офисом или лестницей; присваивается новый ID: {new_id}")
            door.set('id', new_id)
            unassigned_door_counter += 1


def assign_random_ids(root, floor, group_suffix, id_prefix):
    """
    Присваивает случайные уникальные ID элементам в указанной группе.

    :param root: Корневой элемент XML дерева.
    :param floor: Название этажа, например, 'Floor_First'.
    :param group_suffix: Суффикс названия группы, например, 'AllowedLines' или 'Intersections'.
    :param id_prefix: Префикс для ID, например, 'AllowedLine' или 'Intersection'.
    """
    group_id = f"{floor}_{group_suffix}"
    group = root.find(f'.//svg:g[@id="{group_id}"]', namespaces={'svg': 'http://www.w3.org/2000/svg'})
    if group is not None:
        for elem in group.findall('svg:*', namespaces={'svg': 'http://www.w3.org/2000/svg'}):
            new_id = f"{floor}_{id_prefix}_{uuid.uuid4().hex[:4]}"
            print(f"Присваивается новый ID элементу <{elem.tag}>: {new_id}")
            elem.set('id', new_id)
    else:
        print(f"Группа '{group_id}' не найдена в SVG.")


def parse_svg(svg_input_file, floors, threshold):
    """
    Основная функция для парсинга SVG-файла и обновления ID дверей для нескольких этажей.
    """
    # Парсинг SVG
    try:
        tree = ET.parse(svg_input_file)
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"Ошибка при парсинге SVG-файла: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"SVG-файл '{svg_input_file}' не найден.")
        sys.exit(1)

    # Пространства имен SVG
    namespaces = {'svg': 'http://www.w3.org/2000/svg'}

    # Структура данных для всех этажей
    objects_all_floors = {}

    for floor in floors:
        print(f"\nОбработка этажа: {floor}")
        objects = {f"{floor}_Offices": [], f"{floor}_Stairs": []}

        # Извлечение информации об офисах
        offices_group = root.find(f'.//svg:g[@id="{floor}_Offices"]', namespaces)
        if offices_group is not None:
            for office in offices_group.findall('svg:rect', namespaces):
                office_id = office.get('id')
                if office_id:
                    parsed_id = parse_id(office_id)
                    try:
                        x = float(office.get('x', '0'))
                        y = float(office.get('y', '0'))
                        width = float(office.get('width', '0'))
                        height = float(office.get('height', '0'))
                    except ValueError:
                        print(f"Ошибка: Некорректные координаты или размеры для офиса с ID '{office_id}'. Пропуск.")
                        continue
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

        # Извлечение информации о лестницах (если необходимо)
        stairs_group = root.find(f'.//svg:g[@id="{floor}_Stairs"]', namespaces)
        if stairs_group is not None:
            for stair in stairs_group.findall('svg:g', namespaces):
                stair_id = stair.get('id')
                print(f"Обрабатываем лестницу: {stair_id}")
                if stair_id:
                    rects = stair.findall('svg:rect', namespaces)
                    if rects:
                        # Инициализируем границы для всей группы
                        x_min, y_min = float('inf'), float('inf')
                        x_max, y_max = float('-inf'), float('-inf')

                        # Обрабатываем каждый прямоугольник в группе
                        for rect in rects:
                            try:
                                x = float(rect.get('x', '0'))
                                y = float(rect.get('y', '0'))
                                width = float(rect.get('width', '0'))
                                height = float(rect.get('height', '0'))
                            except ValueError:
                                print(f"Err: Bad coords or sizes for rect in stair '{stair_id}'. Skip.")
                                continue

                            # Обновляем минимальные и максимальные границы
                            x_min = min(x_min, x)
                            y_min = min(y_min, y)
                            x_max = max(x_max, x + width)
                            y_max = max(y_max, y + height)

                        if x_min == float('inf') or y_min == float('inf'):
                            print(f"Предупреждение: Лестница '{stair_id}' не содержит валидных прямоугольников.")
                            continue

                        # Рассчитываем итоговые размеры группы
                        stair_position = {
                            'x': x_min,
                            'y': y_min,
                            'width': x_max - x_min,
                            'height': y_max - y_min,
                        }

                        # Добавляем данные о лестнице в objects
                        objects[f"{floor}_Stairs"].append(
                            {
                                'id': stair_id,
                                'parsed_id': parse_id(stair_id),
                                'position': stair_position,
                                'doors': [],  # Инициализация списка дверей
                            }
                        )
                        print(f"Лестница {stair_id} границы: {stair_position}")
        else:
            print(f"Группа '{floor}_Stairs' не найдена в SVG.")

        # Извлечение информации о дверях
        doors_group = root.find(f'.//svg:g[@id="{floor}_Doors"]', namespaces)
        if doors_group is not None:
            assign_new_ids_with_threshold(
                root=root,
                doors_group=doors_group,
                objects=objects,
                stairs_group=stairs_group,
                floor=floor,
                threshold=threshold,
            )
        else:
            print(f"Группа '{floor}_Doors' не найдена в SVG.")

        # Присваиваем случайные ID элементам в группах AllowedLines и Intersections
        assign_random_ids(root, floor, "AllowedLines", "AllowedLine")
        assign_random_ids(root, floor, "Intersections", "Intersection")

        # Добавляем объекты текущего этажа в общую структуру
        objects_all_floors.update(objects)

    # Удаление пространств имен после обработки всех этажей
    remove_namespaces(tree)

    return tree, objects_all_floors


def remove_data_name_attribute(root):
    """
    Рекурсивно удаляет атрибут data-name из всех элементов SVG.
    """
    for elem in root.iter():
        if 'data-name' in elem.attrib:
            del elem.attrib['data-name']
            print(f"Удалён атрибут 'data-name' из элемента <{elem.tag}>")


def save_svg(tree, svg_output_file):
    """
    Сохраняет обновленный SVG-файл.
    """
    # Получаем корневой элемент
    root = tree.getroot()

    # Добавляем атрибуты xmlns и xmlns:svg
    root.set("xmlns", "http://www.w3.org/2000/svg")
    root.set("xmlns:svg", "http://www.w3.org/2000/svg")

    remove_data_name_attribute(root)

    try:
        tree.write(svg_output_file, encoding='utf-8', xml_declaration=True)
        print(f"\nОбновленный SVG сохранен как '{svg_output_file}'")
    except IOError as e:
        print(f"Ошибка при сохранении SVG-файла: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="CLI-приложение для обновления ID дверей в SVG-файле на основе их положения для нескольких этажей."
    )
    parser.add_argument('-i', '--input', type=str, required=True, help="Путь к входному SVG-файлу.")
    parser.add_argument(
        '-o',
        '--output',
        type=str,
        default=None,
        help="Путь к выходному SVG-файлу. По умолчанию '<input>_updated.svg'.",
    )
    parser.add_argument(
        '-f',
        '--floors',
        type=str,
        nargs='+',
        default=['Floor_First', 'Floor_Second', 'Floor_Third', 'Floor_Fourth'],
        help="Имена этажей, используемые в ID групп SVG (например, 'Floor_First' 'Floor_Second').",
    )
    parser.add_argument(
        '-t',
        '--threshold',
        type=int,
        default=10,
        help="Пороговое значение для определения пересечения в пикселях. По умолчанию 10.",
    )

    args = parser.parse_args()

    svg_input_file = args.input
    floors = args.floors
    threshold = args.threshold

    if args.output:
        svg_output_file = args.output
    else:
        # Создаем имя выходного файла на основе имени входного файла
        if svg_input_file.lower().endswith('.svg'):
            svg_output_file = svg_input_file[:-4] + '_updated.svg'
        else:
            svg_output_file = f'{svg_input_file}_updated.svg'

    print(f"Парсинг SVG-файла: {svg_input_file}")
    print(f"Этажи: {', '.join(floors)}")
    print(f"Пороговое значение: {threshold}")
    print(f"Файл вывода: {svg_output_file}")

    updated_tree, objects_all_floors = parse_svg(svg_input_file, floors, threshold)
    save_svg(updated_tree, svg_output_file)

    # Дополнительно: Вывод информации о всех обработанных этажах
    print("\nИнформация об обработанных этажах:")
    for floor, data in objects_all_floors.items():
        if floor.endswith("_Offices") or floor.endswith("_Stairs"):
            obj_type = "офисов" if floor.endswith("_Offices") else "лестниц"
            num_objects = len(data)
            print(f"\nЭтаж: {floor}")
            print(f"  Обнаружено {num_objects} {obj_type}")


if __name__ == "__main__":
    main()
