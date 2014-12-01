import unittest
from openpyxl import load_workbook
from graph import Graph


class GraphTestCase(unittest.TestCase):

    def setUp(self):
        wb = load_workbook("test/test_links.xlsx")
        ws = wb.active
        self.graph = Graph(ws)

    def test_construction(self):
        self.graph = {'a': [('b', 2), ('c', 3)],
                      'b': [('a', 2), ('d', 5), ('e', 2)],
                      'c': [('a', 3), ('e', 5)],
                      'd': [('b', 5), ('e', 1), ('z', 2)],
                      'e': [('b', 2), ('c', 5), ('d', 1), ('z', 4)],
                      'z': [('d', 2), ('e', 4)]}


if __name__ == '__main__':
    unittest.main()
