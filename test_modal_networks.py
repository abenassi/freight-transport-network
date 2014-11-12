import unittest
import os
from modules.builder import RailwayNetworkBuilder
from modal_networks import RailwayNetwork


class RailwayNetworkTestCase(unittest.TestCase):

    def setUp(self):

        # locations to excel files test data
        XL_PARAMETERS = os.path.join(os.path.dirname(__file__),
                                     "test_data/railway_parameters.xlsx")
        XL_OD_PAIRS = os.path.join(os.path.dirname(__file__),
                                   "test_data/railway_od_pairs.xlsx")
        XL_LINKS = os.path.join(os.path.dirname(__file__),
                                "test_data/railway_links.xlsx")
        XL_PATHS = os.path.join(os.path.dirname(__file__),
                                "test_data/railway_paths.xlsx")

        # create test builder
        builder = RailwayNetworkBuilder(xl_parameters=XL_PARAMETERS,
                                        xl_od_pairs=XL_OD_PAIRS,
                                        xl_links=XL_LINKS,
                                        xl_paths=XL_PATHS)

        # create network
        self.rn = RailwayNetwork(builder)

    def test_get_total_tons(self):
        self.assertAlmostEqual(self.rn.get_total_tons(), 22036200.0)

    def test_get_total_ton_km(self):
        self.assertAlmostEqual(self.rn.get_total_ton_km(), 11018100000.0,
                               delta=10000)

    def test_get_dimensions(self):
        dimensions = self.rn.get_dimensions()
        self.assertEqual(dimensions["total"], 15121.0)
        self.assertEqual(dimensions["low"], 15121.0)
        self.assertEqual(dimensions["high"], 0.0)

    def test_get_average_distance(self):
        distance = self.rn.get_average_distance()
        self.assertAlmostEqual(distance, 500.0, delta=1)

    def test_calc_optimized_mobility_cost(self):
        self.rn.calc_optimized_mobility_cost()
        mobility_cost = self.rn.get_costs_tk()["mob"]["total_mobility"]
        self.assertAlmostEqual(mobility_cost, 0.018427133, delta=0.0001)

    def test_calc_infrastructure_cost(self):
        self.rn.calc_optimized_mobility_cost()
        self.rn.calc_infrastructure_cost()
        self.assertAlmostEqual(self.rn.get_total_cost_tk(), 0.04480806,
                               delta=0.0002)


def main():
    unittest.main()

if __name__ == '__main__':
    main()

