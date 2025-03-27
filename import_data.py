import json
import uuid

# Типы объектов для маппинга
OBJECT_TYPE_MAPPING = {
    "cabinet": 1,
    "department": 2,
    "man-toilet": 3,
    "woman-toilet": 4,
    "stair": 5,
    "wardrobe": 6,
    "gym": 7,
}

# ID этажей
FLOOR_MAPPING = {
    "First": "d33d56e3-aca8-4b62-b34a-9e3882276f75",
    "Second": "4ccb7c2d-0bb2-49e0-828f-5b2c43787ee5",
    "Third": "acc38768-c209-4702-957d-778e59f875f3",
    "Fourth": "517650f2-3e3a-42d0-b6e9-6c8e7271b096",
}

# Загрузка JSON-файла
with open("plan_combined.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# SQL-запросы
sql_objects = []
sql_doors = []
sql_object_doors = []

# Обход объектов из JSON
for obj in data["objects"]:
    object_id = uuid.uuid4()
    floor_id = FLOOR_MAPPING.get(obj['parsed_id']['floor'], "NULL")
    if floor_id == "NULL":
        print(f"Не найден этаж: {obj['parsed_id']['floor']}")
        continue
    object_name = obj['parsed_id']['detail']
    object_alias = obj['id']
    x, y = obj['position']['x'], obj['position']['y']
    width, height = obj['position']['width'], obj['position']['height']

    # Определение object_type_id по parsed_id['detail']
    object_type_id = OBJECT_TYPE_MAPPING.get(object_name.lower(), 1)

    sql_objects.append(
        f"""
        INSERT INTO objects (id, name, alias, description, x, y, width, height, object_type_id, floor_id) 
        VALUES ('{object_id}', '{object_name}', '{object_alias}', NULL, {x}, {y}, {width}, {height}, {object_type_id}, '{floor_id}');
    """.strip()
    )

    # Обход дверей
    for door in obj.get("doors", []):
        door_id = uuid.uuid4()
        dx, dy = door['position']['x'], door['position']['y']
        dwidth, dheight = door['position']['width'], door['position']['height']

        sql_doors.append(
            f"""
            INSERT INTO doors (id, x, y, width, height) 
            VALUES ('{door_id}', {dx}, {dy}, {dwidth}, {dheight});
        """.strip()
        )

        sql_object_doors.append(
            f"""
            INSERT INTO object_doors (object_id, door_id) 
            VALUES ('{object_id}', '{door_id}');
        """.strip()
        )

# Запись в SQL-файл
with open("insert_data.sql", "w", encoding="utf-8") as f:
    f.write("\n".join(sql_objects) + "\n\n")
    f.write("\n".join(sql_doors) + "\n\n")
    f.write("\n".join(sql_object_doors) + "\n\n")

print("SQL-скрипт сгенерирован: insert_data.sql")
