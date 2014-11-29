import unittest
from link import BaseLink
from od import OD
from path import Path


class ODTestCase(unittest.TestCase):

    """Test construction of od pair."""

    def setUp(self):
        self.od = OD("70-68", 333906, "068-069-070", "ancha")

    def test_nodes(self):
        self.assertEqual(self.od.nodes, [68, 70])

    def test_path(self):
        self.assertEqual(self.od.path, "068-069-070")

    def test_path_nodes(self):
        self.assertEqual(self.od.path_nodes, [68, 69, 70])

    def test_links(self):
        self.assertEqual(self.od.links, ['68-69', '69-70'])

    def test_get_safe_id(self):
        self.assertEqual(self.od._get_safe_id("50-10"), "10-50")


class OdCostTestCase(unittest.TestCase):

    """Test od costs management."""

    def setUp(self):
        self.od = OD("70-68", 1, "068-069-070", "ancha")

    def test_get_none_deposit_cost(self):
        self.assertEqual(self.od.cost.deposit, None)

    def test_set_and_get_deposit_cost(self):
        self.od.cost.deposit = 1000
        self.assertEqual(self.od.cost.deposit, 1000)

    def test_set_and_get_short_freight_cost(self):
        self.od.cost.short_freight_cost = 1000
        self.assertEqual(self.od.cost.short_freight_cost, 1000)

    def test_set_and_get_immo_value_cost(self):
        self.od.cost.immo_value_cost = 1000
        self.assertEqual(self.od.cost.immo_value_cost, 1000)


class OdTonsTestCase(unittest.TestCase):

    """Test construction of od pair."""

    def setUp(self):
        self.od = OD("70-68", 1000, "068-069-070", "ancha")

    def test_add_and_get_original_tons(self):
        self.od.tons.add_original(1000)
        self.assertEqual(self.od.tons.get_original(), 2000)

    def test_project(self):
        self.od.tons.project(2.0)
        self.assertEqual(self.od.tons.get_original(), 2000)

    def test_revert_project(self):
        self.od.tons.project(2.0)
        self.od.tons.revert_project()
        self.assertEqual(self.od.tons.get_original(), 1000)


class PathTestCase(unittest.TestCase):

    """Test construction path."""

    def setUp(self):
        self.path = Path("68-70", "068-069-070", "unica")
        self.links = {"68-69": {"unica": BaseLink("68-69", 100, "unica")},
                      "69-70": {"unica": BaseLink("68-69", 200, "unica")}}

    def test_calc_distance(self):
        distance = self.path.calc_distance(self.links)
        self.assertEqual(distance, 300)


if __name__ == '__main__':
    unittest.main()
