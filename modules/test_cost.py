import unittest
import os
import sys
from railway_cost import RailwayNetworkCost
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

    # GENERAL cost tests
    def test_calc_total_ton_km(self):
        self.assertAlmostEqual(self.nc._calc_total_ton_km(), self.load_tk,
                               delta=10000)

    # INFRASTRUCTURE cost tests
    def test_cost_infrast_maint(self):
        infrast_maint_cost = self.nc._cost_infrast_maint(self.gross_tk,
                                                         self.dist)
        self.assertAlmostEqual(infrast_maint_cost, 47989846.78, delta=2000000)

    def test_capital_recovery_factor(self):
        int_rate = 0.08
        use_life = 30
        crf = self.nc._capital_recovery_factor(int_rate, use_life)
        self.assertAlmostEqual(crf, 0.08882743338727227)

    def test_cost_eac_track(self):
        # FAINTERU base case with main track parameters
        track_eac = self.nc._cost_eac_track(self.main_gross_tk, self.main_dist)
        self.assertAlmostEqual(track_eac, 232400036.0, delta=10)

        # FAINTERU density * 3.16 with main track parameters
        track_eac = self.nc._cost_eac_track(45704866707, self.main_dist)
        self.assertAlmostEqual(track_eac, 492564218, delta=10)

        # FAINTERU density * 3.16 with secondary track parameters
        track_eac = self.nc._cost_eac_track(12563761436, self.secondary_dist)
        self.assertAlmostEqual(track_eac, 227724904, delta=10)

        track_eac = self.nc._cost_eac_track(303670609022.56, self.dist)
        self.assertAlmostEqual(track_eac, 1807731647, delta=10)

    def test_calc_number_of_detours(self):
        num_detours = self.nc._calc_number_of_detours(self.gross_tk, self.dist)
        self.assertAlmostEqual(num_detours, 76.83, 2)

    def test_cost_eac_track_with_detours(self):
        density = 2008271.0
        distance = 1.0
        cost_eac_detour = self.nc._cost_eac_track(density, distance)
        self.assertAlmostEqual(cost_eac_detour, 32268.82, 2)

    def test_cost_detour(self):
        detours_cost = self.nc._cost_detour(self.gross_tk, self.dist)
        self.assertAlmostEqual(detours_cost, 10357513.22, delta=100000)

    # MOBILITY cost tests
    def test_cost_manpower(self):
        manpower_cost_tk = self.nc.cost_mobility()["manpower"]
        self.assertAlmostEqual(manpower_cost_tk, 0.0010809136373677642, 5)

    def test_cost_mobility(self):
        total_mobility_cost_tk = self.nc.cost_mobility()["total_mobility"]
        self.assertAlmostEqual(total_mobility_cost_tk, 0.018443320134665583, 5)

    # TIME cost tests

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


def main():
    unittest.main()

if __name__ == '__main__':
    main()
