import xml.etree.ElementTree as ET

# Загрузка оригинального SVG
tree = ET.parse('media/улк-5.svg')
root = tree.getroot()

# Определяем SVG namespace
ns = {'svg': 'http://www.w3.org/2000/svg'}
ET.register_namespace('', ns['svg'])

# Получение размеров SVG
print(root.attrib)
width = int(float(root.attrib.get('width', '1000')))
height = int(float(root.attrib.get('height', '1000')))


# Функция для создания линии
def create_line(x1, y1, x2, y2, color='#cccccc', width='1'):
    return ET.Element(
        'line', {'x1': str(x1), 'y1': str(y1), 'x2': str(x2), 'y2': str(y2), 'stroke': color, 'stroke-width': width}
    )


# Добавляем сетку (линии через 500 пикселей)
grid_layer = ET.Element('g', {'id': 'pixel-grid'})

for x in range(0, width + 1, 500):
    grid_layer.append(create_line(x, 0, x, height))

for y in range(0, height + 1, 500):
    grid_layer.append(create_line(0, y, width, y))

# Добавляем сетку как самый нижний слой
root.insert(0, grid_layer)

# Сохраняем новый SVG
tree.write('улк-5_with_grid.svg')
