import unittest
import os
import sys
from cost import RailwayNetworkCost
from cost import RailwayMobilityCost, RailwayInfrastructureCost
from cost import RailwayTimeCost
from builder import RailwayNetworkBuilder

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from modal_networks import RailwayNetwork


class RailwayNetworkCostTestCase(unittest.TestCase):

    def setUp(self):

        root_dir = os.path.dirname(os.path.dirname(__file__))

        # locations to excel files test data
        XL_PARAMETERS = os.path.join(root_dir,
                                     "test_data/railway_parameters.xlsx")
        XL_OD_PAIRS = os.path.join(root_dir,
                                   "test_data/railway_od_pairs.xlsx")
        XL_LINKS = os.path.join(root_dir, "test_data/railway_links.xlsx")
        XL_PATHS = os.path.join(root_dir, "test_data/railway_paths.xlsx")

        # create test builder
        builder = RailwayNetworkBuilder(xl_parameters=XL_PARAMETERS,
                                        xl_od_pairs=XL_OD_PAIRS,
                                        xl_links=XL_LINKS,
                                        xl_paths=XL_PATHS)

        # create network
        self.rn = RailwayNetwork(builder)

        # init object enought fed to test infrastructure methods
        self.nc = RailwayNetworkCost(self.rn)
        self.mob = RailwayMobilityCost(self.rn)
        self.inf = RailwayInfrastructureCost(self.rn)
        self.time = RailwayTimeCost(self.rn)
        self.rn.calc_mobility_requirements()

        # net ton-km to test
        self.load_tk = 11018100000.0

        # gross ton-km to test
        self.gross_tk = 18439439286.0
        self.main_gross_tk = 14463565413.53

        # dist to test
        self.dist = 15121.0
        self.main_dist = 7202.0
        self.secondary_dist = 7919.0

    # INFRASTRUCTURE cost tests
    def test_cost_infrast_maint(self):
        infrast_maint_cost = self.inf._cost_infrast_maint(self.gross_tk,
                                                          self.dist)
        self.assertAlmostEqual(infrast_maint_cost, 40874101.48124131, delta=2000000)

    def test_capital_recovery_factor(self):
        int_rate = 0.08
        use_life = 30
        crf = self.inf._capital_recovery_factor(int_rate, use_life)
        self.assertAlmostEqual(crf, 0.08882743338727227)

    def test_cost_eac_track(self):
        # FAINTERU base case with main track parameters
        track_eac = self.inf._cost_eac_track(self.main_gross_tk,
                                             self.main_dist, True)
        self.assertAlmostEqual(track_eac, 190568029.0, delta=10)

        # FAINTERU density * 3.16 with main track parameters
        track_eac = self.inf._cost_eac_track(45704866707, self.main_dist, True)
        self.assertAlmostEqual(track_eac, 403902659, delta=10)

        # FAINTERU density * 3.16 with secondary track parameters
        track_eac = self.inf._cost_eac_track(12563761436, self.secondary_dist,
                                             True)
        self.assertAlmostEqual(track_eac, 186734421, delta=10)

        track_eac = self.inf._cost_eac_track(303670609022.56, self.dist, True)
        self.assertAlmostEqual(track_eac, 1482339950, delta=10)

    def test_calc_number_of_detours(self):
        num_detours = self.inf._calc_number_of_detours(self.gross_tk,
                                                       self.dist)
        self.assertAlmostEqual(num_detours, 76.83, 2)

    def test_cost_eac_track_with_detours(self):
        density = 2008271.0
        distance = 1.0
        cost_eac_detour = self.inf._cost_eac_track(density, distance, True)
        self.assertAlmostEqual(cost_eac_detour, 26460.433998923036, 2)

    def test_cost_detour(self):
        detours_cost = self.inf._cost_detour(self.gross_tk, self.dist)
        self.assertAlmostEqual(detours_cost, 8226343.6445830725, delta=100000)

    # MOBILITY cost tests
    def test_cost_manpower(self):
        manpower_cost_tk = self.nc.cost_mobility()["manpower"]
        self.assertAlmostEqual(manpower_cost_tk, 0.0008863491826415666, 5)

    def test_cost_mobility(self):
        total_mobility_cost_tk = self.nc.cost_mobility()["total_mobility"]
        self.assertAlmostEqual(total_mobility_cost_tk, 0.015123522510425777, 5)

    # TIME cost tests
    def test_cost_time(self):
        total_time_cost_tk = self.nc.cost_time()["total_time"]
        self.assertAlmostEqual(total_time_cost_tk, 0.011905434303139083)

    # AUXILIAR METHODS
    def _load_from_xl(self, loader_class, xl_name, output_dict):
        """Iterate an excel with data using a specific loader_class and storing
        results to output_dict."""

        for element in loader_class(xl_name):

            # check if element id was already in output_dict
            if element.id not in output_dict:
                output_dict[element.id] = element

            else:
                print "Warning", element.id, "is repeated in", xl_name


if __name__ == '__main__':
    unittest.main()
