import unittest
import xml.etree.ElementTree as ET

from app.services.object_processor import get_objects_map


class TestGetObjectsMap(unittest.TestCase):
    def setUp(self):
        self.all_floors = ["F1", "F2", "F3", "F4"]

    def create_svg_tree(self, elements):
        """Создает XML-дерево для тестов."""
        svg_root = ET.Element("svg")
        for element_id in elements:
            ET.SubElement(svg_root, "g", id=element_id)
        return ET.ElementTree(svg_root)

    def test_valid_offices(self):
        svg_tree = self.create_svg_tree(["F1_Office_101", "F2_Office_202", "F3_Office_303"])
        expected = {
            "F1_Office_101": "Кабинет 101 (1 этаж)",
            "F2_Office_202": "Кабинет 202 (2 этаж)",
            "F3_Office_303": "Кабинет 303 (3 этаж)",
        }
        self.assertEqual(get_objects_map(svg_tree, self.all_floors), expected)

    def test_special_rooms(self):
        svg_tree = self.create_svg_tree(["F1_Office_Kitchen", "F2_Office_Gym", "F3_Office_Dining"])
        expected = {
            "F1_Office_Kitchen": "Кухня (1 этаж)",
            "F2_Office_Gym": "Спортзал (2 этаж)",
            "F3_Office_Dining": "Столовая (3 этаж)",
        }
        self.assertEqual(get_objects_map(svg_tree, self.all_floors), expected)

    def test_stairs(self):
        svg_tree = self.create_svg_tree(["F1_Stairs_A", "F2_Stairs_B", "F3_Stairs_C"])
        expected = {
            "F1_Stairs_A": "Лестница A (1 этаж)",
            "F2_Stairs_B": "Лестница B (2 этаж)",
            "F3_Stairs_C": "Лестница C (3 этаж)",
        }
        self.assertEqual(get_objects_map(svg_tree, self.all_floors), expected)

    def test_ignored_elements(self):
        svg_tree = self.create_svg_tree(["AllowedLines", "Intersections", "Doors", "IDK_Object", "F1_Office_101"])
        expected = {"F1_Office_101": "Кабинет 101 (1 этаж)"}
        self.assertEqual(get_objects_map(svg_tree, self.all_floors), expected)

    def test_toilets(self):
        svg_tree = self.create_svg_tree(["F1_Office_Toilet_shkn", "F2_Office_Toilet_fizhim", "F3_Office_Toilet"])
        expected = {
            "F1_Office_Toilet_shkn": "Туалет (Левое крыло) (1 этаж)",
            "F2_Office_Toilet_fizhim": "Туалет (Правое крыло) (2 этаж)",
            "F3_Office_Toilet": "Туалет (3 этаж)",
        }
        self.assertEqual(get_objects_map(svg_tree, self.all_floors), expected)

    def test_empty_svg(self):
        svg_tree = self.create_svg_tree([])
        self.assertEqual(get_objects_map(svg_tree, self.all_floors), {})

    def test_invalid_format(self):
        svg_tree = self.create_svg_tree(["InvalidElement"])
        self.assertEqual(get_objects_map(svg_tree, self.all_floors), {})


if __name__ == "__main__":
    unittest.main()
