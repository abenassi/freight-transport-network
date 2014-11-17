import unittest
from dijkstra import dijkstra


class DijkstraTestCase(unittest.TestCase):

    def setUp(self):

        self.G1 = {  # Rosen, Figure 4 (pp. 559)
            'a': [('b', 4), ('c', 2)],
            'b': [('a', 4), ('c', 1), ('d', 5)],
            'c': [('a', 2), ('b', 1), ('d', 8), ('e', 10)],
            'd': [('b', 5), ('c', 8), ('e', 2), ('z', 6)],
            'e': [('c', 10), ('d', 2), ('z', 3)],
            'z': [('d', 6), ('e', 3)],
        }

        self.G2 = {  # Rosen, Ex. 8.6-2 (pp. 562)
            'a': [('b', 2), ('c', 3)],
            'b': [('a', 2), ('d', 5), ('e', 2)],
            'c': [('a', 3), ('e', 5)],
            'd': [('b', 5), ('e', 1), ('z', 2)],
            'e': [('b', 2), ('c', 5), ('d', 1), ('z', 4)],
            'z': [('d', 2), ('e', 4)],
        }

    def test_dijkstra(self):
        """Test dijkstra implementation return correct distance and path."""

        # test with graph 1
        distance, path = dijkstra(self.G1, 'a', 'z')
        self.assertEqual(distance, 13)
        self.assertEqual(path, ['a', 'c', 'b', 'd', 'e', 'z'])

        # test with graph 2
        distance, path = dijkstra(self.G2, 'a', 'z')
        self.assertEqual(distance, 7)
        self.assertEqual(path, ['a', 'b', 'e', 'd', 'z'])


def main():
    unittest.main()

if __name__ == '__main__':
    main()
