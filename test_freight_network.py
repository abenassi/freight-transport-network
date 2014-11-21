import unittest
from freight_network import FreightNetwork
from modal_networks import RailwayNetwork, RoadwayNetwork
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
            start_ton = self.fn.rail.get_od("1-3", 1).get_ton()
        else:
            start_ton = 0.0

        # derive
        coeff = 0.5
        derived_rail_od = self.fn.derive_to_railway(od_road, coeff)

        # check out tons left in road and increased in rail
        final_ton = self.fn.rail.get_od("1-3", 1).get_ton()
        self.assertEqual(start_ton + coeff * road_ton, final_ton)
        self.assertEqual((1- coeff) * road_ton, od_road.get_ton())

    def test_get_derivation_coefficient(self):
        expected_coefficient = 0.51405340750397721
        tons = 1412010
        dist = 216
        categ = 1
        coefficient = self.fn._get_derivation_coefficient(tons, dist, categ)
        self.assertAlmostEqual(coefficient, expected_coefficient)


if __name__ == '__main__':
    unittest.main()
