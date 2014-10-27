import unittest
from railway_cost import NetworkCost
from railway_parameters import Parameter
from railway_link import Link
from railway_rolling_material import RollingMaterial
from railway_xl_input import XlLoadParam


class NetworkCostTestCase(unittest.TestCase):

    def setUp(self):

        # load parameters to test
        XL_PARAMETERS = "test_data/test_railway_parameters.xlsx"
        params = {}
        self._load_from_xl(XlLoadParam, XL_PARAMETERS, params)

        # create link representing main network
        link = Link("1-3", 7202.0, "ancha")
        link.ton = 1200000
        links = {"1-3": {"ancha": link}}

        # create locomotives object
        locoms = RollingMaterial()
        locoms.running = 137.91 * 1564.29
        locoms.idle_heads = 137.91 * 30 * 125.14
        locoms.idle_turnout = 137.91 * 1250.14
        locoms.speed = 40  # (km/h)
        locoms.availability = 6570  # (hr/year)
        locoms.capacity = 2400  # (ton)
        locoms.head_stops_time = 15  # (hr/head_stop)
        locoms.turnout_time = 4  # (hr/turnout_stop)
        locoms.turnout_freq = 200  # (km between turnouts

        # create wagons object
        wagons = RollingMaterial()
        wagons.running = 15313.81 * 535.33
        wagons.idle_heads = 15313.81 * 180 * 42.83
        wagons.idle_turnout = 15313.81 * 428.27
        wagons.speed = 40  # (km/h)
        wagons.availability = 8672  # (hr/year)
        wagons.capacity = 60  # (ton)
        wagons.head_stops_time = 15  # (hr/head_stop)
        wagons.turnout_time = 4  # (hr/turnout_stop)
        wagons.turnout_freq = 200  # (km between turnout_stop

        # init object enought fed to test infrastructure methods
        self.nc = NetworkCost(params, links=links, locoms=locoms,
                              wagons=wagons)

        # net ton-km to test
        self.load_tk = 8642400000.0

        # gross ton-km to test
        self.gross_tk = 14463565413.5338

        # dist to test
        self.dist = 7202.0

    def test_cost_infrast_maint(self):
        infrast_maint_cost = self.nc._cost_infrast_maint(self.gross_tk,
                                                         self.dist)
        self.assertAlmostEqual(infrast_maint_cost,
                               0.00314429044 * self.load_tk, delta=10)

    def test_cost_eac_track(self):
        track_eac = self.nc._cost_eac_track(self.gross_tk, self.dist)
        self.assertAlmostEqual(track_eac,
                               0.026890682715 * self.load_tk, delta=10)

    def test_cost_detour(self):
        detours_cost_tk = self.nc._cost_detour(self.gross_tk, self.dist)
        self.assertAlmostEqual(detours_cost_tk,
                               0.0004562500000 * self.load_tk, delta=10)

    def test_calc_total_ton_km(self):
        self.assertAlmostEqual(self.nc._calc_total_ton_km(), self.load_tk)

    def test_cost_mobility(self):
        total_cost_mobility = self.nc.cost_mobility()["total_mobility"]
        self.assertAlmostEqual(total_cost_mobility, 0.025247726649)

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
