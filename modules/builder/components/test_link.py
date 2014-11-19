import unittest
from link import Link, RailwayLink, RoadwayLink


class LinkTestCase(unittest.TestCase):
    """Test construction of a base Link."""

    def setUp(self):
        self.link = Link("1009-1003", 150.4, "ancha")

    def test_add_original_ton(self):
        """Test method to add tons to a link."""

        self.link.add_original_ton(500)
        self.assertTrue(self.link.get_ton(), 500)

        self.link.add_original_ton(500)
        self.assertTrue(self.link.get_ton(), 1000)


class RailwayLinkTestCase(unittest.TestCase):
    """Test methods of RailwayLink."""

    def setUp(self):
            self.link = RailwayLink("1009-1003", 1000, "ancha")

    def test_regroup(self):
        """Test method to regroup idle wagons in railway link."""

        self.link.add_idle_cap_regroup(500)
        self.link.regroup(250)
        self.assertTrue(self.link.get_idle_cap_regroup(), 250)

    def test_revert_regroup(self):
        """Test method to revert regroup of idle wagons in railway link."""

        self.link.revert_regroup(250)
        self.assertTrue(self.link.get_idle_cap_regroup(), 500)


def main():
    unittest.main()

if __name__ == '__main__':
    main()