import unittest
from freight_network import FreightNetwork
from modules.builder.components import OD


class FreightNetworkTestCase(unittest.TestCase):

    def setUp(self):

        # initiate object
        self.fn = FreightNetwork()

    def test_derive_to_railway(self):
        "Test method to derive tons to an od pair from other transport mode."

        # create road od pair
        road_ton = 10000000
        od_road = OD("1-3", road_ton, None, None, None, 1)

        # check out tons already in rail mode
        if "1-3" in self.fn.rail.od_pairs:
            start_ton = self.fn.rail.get_od("1-3", 1).tons.get()
        else:
            start_ton = 0.0

        # derive
        coeff = 0.5
        self.fn.derive.od_to_railway(od_road, coeff)

        # check out tons left in road and increased in rail
        final_ton = self.fn.rail.get_od("1-3", 1).tons.get()
        self.assertEqual(start_ton + coeff * road_ton, final_ton)
        self.assertEqual((1 - coeff) * road_ton, od_road.tons.get())

    def test_get_derivation_coefficient(self):
        expected_coefficient = 0.41124272600318179
        tons = 1412010
        dist = 216
        categ = 1
        coefficient = self.fn.derive._get_derivation_coefficient(tons, dist,
                                                                 categ)
        self.assertAlmostEqual(coefficient, expected_coefficient)

    def test_consistent_result(self):

        # no overlapping on railway max derivation
        self.fn.derive.all_to_railway()
        self.fn.cost_network()
        total_cost_1 = self.fn.get_total_cost()

        self.fn.derive.all_to_railway()
        self.fn.cost_network()
        total_cost_2 = self.fn.get_total_cost()

        self.assertEqual(total_cost_1, total_cost_2)

        # no overlapping on roadway max derivation
        self.fn.derive.all_to_roadway()
        self.fn.cost_network()
        total_cost_3 = self.fn.get_total_cost()

        self.fn.derive.all_to_roadway()
        self.fn.cost_network()
        total_cost_4 = self.fn.get_total_cost()

        self.assertEqual(total_cost_3, total_cost_4)

        # consistency in successive derivations
        self.fn.derive.all_to_railway()
        self.fn.cost_network()
        total_cost_5 = self.fn.get_total_cost()

        self.fn.derive.all_to_roadway()
        self.fn.cost_network()
        total_cost_6 = self.fn.get_total_cost()

        self.fn.derive.all_to_railway()
        self.fn.cost_network()
        total_cost_7 = self.fn.get_total_cost()

        self.fn.derive.all_to_roadway()
        self.fn.cost_network()
        total_cost_8 = self.fn.get_total_cost()

        self.assertEqual(total_cost_5, total_cost_7)
        self.assertEqual(total_cost_6, total_cost_8)


if __name__ == '__main__':
    unittest.main()
