import unittest
import os
from railway_cost import RailwayNetworkCost
from builder.components import Parameter, RailwayLink, RollingMaterial
from builder.railway_network_builder import XlLoadParam


class RailwayNetworkCostTestCase(unittest.TestCase):

    def setUp(self):

        # load parameters to test
        XL_PARAMETERS = os.path.join(os.path.dirname(__file__),
                                     "test_data/test_railway_parameters.xlsx")
        params = {}
        self._load_from_xl(XlLoadParam, XL_PARAMETERS, params)

        # create link representing main network
        link = RailwayLink("1-3", 15121.0, "ancha")
        link.ton = 728662.0
        links = {"1-3": {"ancha": link}}

        # create locomotives object
        locoms = RollingMaterial()
        locoms.running = 215737.0
        locoms.idle_heads = 517767.86
        locoms.idle_turnout = 172589.29
        locoms.speed = 40  # (km/h)
        locoms.availability = 6570  # (hr/year)
        locoms.capacity = 1276.8  # (ton)
        locoms.head_stops_time = 15  # (hr/head_stop)
        locoms.turnout_time = 4  # (hr/turnout_stop)
        locoms.turnout_freq = 200  # (km between turnouts)

        # create wagons object
        wagons = RollingMaterial()
        wagons.running = 8197991.0
        wagons.idle_heads = 118051071.0
        wagons.idle_turnout = 6558393.0
        wagons.speed = 40  # (km/h)
        wagons.availability = 8672.4  # (hr/year)
        wagons.capacity = 33.6  # (ton)
        wagons.head_stops_time = 90  # (hr/head_stop)
        wagons.turnout_time = 4  # (hr/turnout_stop)
        wagons.turnout_freq = 200  # (km between turnout_stop

        # init object enought fed to test infrastructure methods
        self.nc = RailwayNetworkCost(params, links=links, locoms=locoms,
                                     wagons=wagons)

        # net ton-km to test
        self.load_tk = 11018100000.0

        # gross ton-km to test
        self.gross_tk = 18439439286.0
        self.main_gross_tk = 14463565413.53

        # dist to test
        self.dist = 15121.0
        self.main_dist = 7202.0

    # GENERAL cost tests
    def test_calc_total_ton_km(self):
        self.assertAlmostEqual(self.nc._calc_total_ton_km(), self.load_tk,
                               delta=2000)

    # INFRASTRUCTURE cost tests
    def test_cost_infrast_maint(self):
        infrast_maint_cost = self.nc._cost_infrast_maint(self.gross_tk,
                                                         self.dist)
        self.assertAlmostEqual(infrast_maint_cost, 47989846.78, delta=2000000)

    def test_cost_eac_track(self):
        track_eac = self.nc._cost_eac_track(self.main_gross_tk, self.main_dist)
        self.assertAlmostEqual(track_eac, 232400036.0, delta=10)

    def test_cost_detour(self):
        detours_cost_tk = self.nc._cost_detour(self.gross_tk, self.dist)
        self.assertAlmostEqual(detours_cost_tk, 8278748.0, delta=10)

    # MOBILITY cost tests
    def test_cost_manpower(self):
        manpower_cost_tk = self.nc.cost_mobility()["manpower"]
        self.assertAlmostEqual(manpower_cost_tk, 0.00107202)

    def test_cost_mobility(self):
        total_mobility_cost_tk = self.nc.cost_mobility()["total_mobility"]
        self.assertAlmostEqual(total_mobility_cost_tk, 0.01837137, 5)

    # AUXILIAR METHODS
    def _load_from_xl(self, loader_class, xl_name, output_dict):
        """Iterate an excel with data using a specific loader_class and storing
        results to output_dict."""

        for element in loader_class(xl_name):

            # check if element id was already in output_dict
            if not element.id in output_dict:
                output_dict[element.id] = element

            else:
                print "Warning", element.id, "is repeated in", xl_name


def main():
    unittest.main()

if __name__ == '__main__':
    main()
