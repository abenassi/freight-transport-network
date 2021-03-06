import unittest
import os
from modules.builder import RailwayNetworkBuilder
from modal_networks import RailwayNetwork


# @unittest.skip("RailwayNetwork test skipped")
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
        self.assertAlmostEqual(self.rn.ton, 22036200.0)

    def test_get_total_ton_km(self):
        self.assertAlmostEqual(self.rn.ton_km, 11018100000.0,
                               delta=10000)

    def test_density(self):
        self.assertAlmostEqual(self.rn.density, 728662, delta=10)

    def test_get_dimensions(self):
        self.assertEqual(self.rn.dimension, 15121.0)
        self.assertEqual(self.rn.high_density_dimension, 0.0)
        self.assertEqual(self.rn.low_density_dimension, 8121.0)

    def test_get_average_distance(self):
        distance = self.rn.average_distance
        self.assertAlmostEqual(distance, 500.0, delta=1)

    def test_calc_optimized_mobility_cost(self):
        self.rn.calc_optimized_mobility_cost()
        mobility_cost = self.rn.costs["mob"]["total_mobility"]
        self.assertAlmostEqual(mobility_cost, 0.0151102490303395, delta=0.0001)

    def test_calc_infrastructure_cost(self):
        self.rn.calc_optimized_mobility_cost()
        self.rn.calc_infrastructure_cost()
        self.assertAlmostEqual(self.rn.total_cost_tk, 0.0424800010113669,
                               delta=0.0002)


class BaseModalNetworkTestCase(unittest.TestCase):

    def setUp(self):
        XL_PATHS = os.path.join(os.path.dirname(__file__),
                                "test_data/railway_paths2.xlsx")

        # create test builder
        builder = RailwayNetworkBuilder(xl_paths=XL_PATHS)
        self.rn = RailwayNetwork(builder)

    def test_find_shortest_path(self):

        expected_path = "21-19-20-58-56"

        path_obj = self.rn.find_shortest_path("21-56")
        path = path_obj.path

        self.assertEqual(path, expected_path)

    @unittest.skip("Integration test skipped")
    def test_find_shortest_path_integrated(self):

        ok_paths = 0
        different_paths = 0
        for exp_path_obj in self.rn.paths.values():
            expected_path = exp_path_obj.path
            path = self.rn.find_shortest_path(exp_path_obj.id).path

            # count matched and non-matched paths
            if path == expected_path:
                ok_paths += 1

            else:
                different_paths += 1
                # if different_paths < 100:
                #     print expected_path, path

        # print "ok paths:", ok_paths, "different paths:", different_paths

        self.assertEqual(ok_paths, 3037)
        self.assertEqual(different_paths, 20)


if __name__ == '__main__':
    unittest.main()
