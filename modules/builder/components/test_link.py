import unittest
from link import BaseLink, RailwayLink


class LinkTestCase(unittest.TestCase):

    """Test construction of a base Link."""

    def setUp(self):
        self.link = BaseLink("1009-1003", 150.4, "ancha")

    def test_add_original_ton(self):
        """Test method to add original tons to a link."""

        self.link.tons.add_original(500, 1, "1-3")
        self.assertEqual(self.link.tons.get(), 500)

    def test_add_derived_ton(self):
        """Test method to add derived tons to a link."""

        self.link.tons.add_derived(500, 1, "1-3")
        self.assertEqual(self.link.tons.get(), 500)

    def test_get_ton(self):
        """Test adding different tons a getting them filtered."""

        self.link.tons.add_original(500, 1, "1-3")
        self.link.tons.add_original(500, 3, "1-5")
        self.link.tons.add_original(500, 3, "1-7")
        self.link.tons.add_original(600, 4, "1-7")
        self.link.tons.add_derived(100, 5, "1-7")
        self.link.tons.add_derived(200, 5, "1-5")
        self.link.tons.add_derived(200, 3, "1-5")

        # aggregated result
        self.assertEqual(self.link.tons.get(), 2600)

        # by mode
        mode = "original"
        ton = self.link.tons.get(modes=mode)
        self.assertEqual(ton, 2100)

        # by category
        category = 3
        ton = self.link.tons.get(categories=category)
        self.assertEqual(ton, 1200)

        # by id_od
        id_od = "1-7"
        ton = self.link.tons.get(id_ods=id_od)
        self.assertEqual(ton, 1200)

        # by mode and category
        mode = "original"
        category = 3
        ton = self.link.tons.get(modes=mode, categories=category)
        self.assertEqual(ton, 1000)

        # by mode, category and id_od
        mode = "original"
        category = 3
        id_od = "1-7"
        ton = self.link.tons.get(modes=mode, categories=category, id_ods=id_od)
        self.assertEqual(ton, 500)


class RailwayLinkTestCase(unittest.TestCase):

    """Test methods of RailwayLink."""

    def setUp(self):
        self.link = RailwayLink("1009-1003", 1000, "ancha")

    def test_regroup(self):
        """Test method to regroup idle wagons in railway link."""

        self.link.idle_capacity_regroup = 500
        self.link.regroup(250)
        self.assertTrue(self.link.idle_capacity_regroup, 250)

    def test_revert_regroup(self):
        """Test method to revert regroup of idle wagons in railway link."""

        self.link.revert_regroup(250)
        self.assertTrue(self.link.idle_capacity_regroup, 500)

if __name__ == '__main__':
    unittest.main()
