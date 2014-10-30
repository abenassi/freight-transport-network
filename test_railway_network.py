import unittest
from railway_network import RailwayNetwork
from modules.builder.components import OD


class RailwayNetworkTestCase(unittest.TestCase):

    def setUp(self):

        # initiate object
        self.rn = RailwayNetwork()

    def test_get_derivation_coefficient(self):
        "Test method to get derivation coefficient."

        od_max = OD("70-68", 119999, "068-069-070", "ancha", 499)
        od_min = OD("70-68", 5001, "068-069-070", "ancha", 201)

        self.assertAlmostEqual(self.rn._get_derivation_coefficient(od_max),
                               0.798115670789)
        self.assertAlmostEqual(self.rn._get_derivation_coefficient(od_min),
                               0.00188432921117)


def main():
    unittest.main()

if __name__ == '__main__':
    main()
