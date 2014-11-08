from modal_networks import RailwayNetwork, RoadwayNetwork
import sys
import numpy as np
from pprint import pprint

"""
    This is the main module that will be visible to the user. Exposes
    FreightNetwork class with methods to derive traffic between freight
    transport modal networks and to cost the overall network. It will be able
    to try different traffic configurations to find the one with lowest
    overall cost.
"""


class FreightNetwork():

    """Represents a freight network with rail and road modes of transport.

    FreightNetwork uses RailwayNetwork and RoadNetwork objects to represent a
    bimodal freight transport network. It uses those classes to cost all
    freight network and can derive traffic from one mode of transport to the
    other, exploring changes in overall cost of different traffic
    configurations."""

    def __init__(self, railway_network, roadway_network):
        self.rail = railway_network
        self.road = roadway_network
        self.min_cost = sys.maxint
        self.max_cost = 0.0

    # PUBLIC
    def cost_network(self):
        """Cost total freight transport network."""
        pass

    def derive_to_railway(self, od_road, coeff):
        """Derive a road od pair to railway mode.

        Args:
            od_road: Road OD pair to be derived.
            coeff: Percentage of tons to be derived.
        """

        # first, calculate tons to be derived
        derived_tons = od_road.get_ton() * coeff

        # derive tons from od_road pair to od_rail pair
        od_rail = self.rail.get_od(od_road.get_id(), od_road.get_category())
        od_road.derive_ton(od_rail, coeff)

        # remove tons from road links used by road od_pair
        for id_road_link in od_road.get_links():
            road_link = self.road.get_link(id_road_link)[od_road.get_gauge()]
            road_link.remove_original_ton(derived_tons)

        # add derived tons to rail links, used by rail od_pair
        for id_rail_link in od_rail.get_links():
            rail_link = self.rail.get_link(id_rail_link)[od_rail.get_gauge()]
            rail_link.add_derived_ton(derived_tons)

    def derive_to_roadway(self, od_rail, coeff):
        """Derive a rail od pair to roadway mode.

        Args:
            od_rail: Rail OD pair to be derived.
            coeff: Percentage of tons to be derived.
        """
        pass

    def derive_all_to_railway(self):
        """Derive all possible road od_pairs from road mode to rail mode."""

        # iterate road od_pairs
        for road_od in self.road.iter_od_pairs():

            # check if od_pair is derivable
            if self._od_pair_is_derivable(road_od):

                # calculate proportion of tons to be derived
                coeff = self._get_derivation_coefficient(road_od)

                # derive road tons to railway
                self.derive_to_railway(road_od, coeff)

    def derive_all_to_roadway(self):
        """Derive all possible rail od pairs from rail mode to road mode."""
        pass

    def free_railway_link(self, link):
        """Derive all rail OD pairs using a link to roadway mode."""
        pass

    def minimize_network_cost(self):
        """Find the modal split with minimum overall cost.

        Derive traffic from one mode to the other looking for the minimum
        overall cost of freight transportation."""
        pass

    def report_to_excel(self, add_tag=None):
        """Make a report of RailwayNetwork and RoadNetwork results.

        At any moment, freeze the status of RailwayNetwork and RoadNetwork
        into excel reports.

        Args:
            add_tag: String to be added to name of excel report, to identify
            the type of analysis being reported.
        """
        pass

    # PRIVATE
    def _od_pair_is_derivable(self, od):
        """Indicate if an od pair is derivable or not.

        Args:
            od: OD pair that will be checked to be derivable to railway.
        """

        # firts check origin != destination
        if od.is_intrazone():
            return False

        # check if there is an operable railway path for the od pair
        has_railway_path = self.rail.has_railway_path(od)
        if not has_railway_path:
            return False

        # check if od pair meet minimum tons adn distance to be derivable
        min_ton = od.get_ton() > self.rail.params["min_tons_to_derive"].value
        min_dist = od.get_dist() > self.rail.params["min_dist_to_derive"].value

        # check if railway path distance is not excesively longer than road
        max_diff = self.rail.params["max_path_difference"].value
        dist_rail = self.rail.get_path_distance(od)
        dist_road = self.road.get_path_distance(od)
        railway_path_is_plausible = abs(dist_rail / dist_road - 1) < max_diff

        is_derivable = min_ton and min_dist and railway_path_is_plausible

        return is_derivable

    def _get_derivation_coefficient(self, od):
        """Calculate the proportion of an od pair that will be derived.

        The proportion is the vectorial distance an od_pair has from minimum
        derivation conditions (minimum distance and tons in wich derivation is
        zero) over total vectorial distance from minimum to maximum conditions
        (in wich derivation is maximum) passing throug the point represented
        by distance and tons of od pair passed as argument.

        Args:
            od: Roadway od pair that will be derived to Railway mode.
        """

        # assign parameters to short variables
        max_dist = float(self.rail.params["dist_of_max_derivation"].value)
        min_dist = float(self.rail.params["min_dist_to_derive"].value)
        max_tons = float(self.rail.params["tons_of_max_derivation"].value)
        min_tons = float(self.rail.params["min_tons_to_derive"].value)
        max_deriv = float(self.rail.params["max_derivation"].value)

        # assign max derivation if distance and tons are greater than max
        if od.get_dist() >= max_dist and od.get_ton() >= max_tons:
            deriv_coefficient = max_deriv

        # assign zero derivation if distance and tons are lower than min
        elif od.get_dist() <= min_dist and od.get_ton() >= min_tons:
            deriv_coefficient = 0.0

        # interpolate derivation coefficient otherwise
        else:

            # calculate substitution coefficient for tons / dist
            coef_ton_dist = (max_tons - min_tons) / (max_dist - min_dist)

            # get tons and distance relevant to interpolate
            # if one of the two dimensions exceeds maximum, maximum will be
            # used
            tons = min(od.get_ton(), max_tons)
            dist = min(od.get_dist(), max_dist)

            # transform dist in tons unit with substitution coefficient
            dist_in_tons = dist * coef_ton_dist
            max_dist_in_tons = max_dist * coef_ton_dist
            min_dist_in_tons = min_dist * coef_ton_dist

            # create vectors
            od_vector = (tons, dist_in_tons)
            max_vector = (max_tons, max_dist_in_tons)
            min_vector = (min_tons, min_dist_in_tons)

            # calculate vectorial distances
            dist_to_min = np.linalg.norm(np.subtract(od_vector, min_vector))
            dist_to_max = np.linalg.norm(np.subtract(max_vector, od_vector))
            total_dist = dist_to_min + dist_to_max

            # calculate coefficient as % of total vectorial distance
            deriv_coefficient = max_deriv * (dist_to_min / total_dist)

        return deriv_coefficient


def main():
    """Some methods used here still does not work. Further design and
    implementation points to support this main method wich represent the user
    case."""

    # initialize freight transport networks
    rail = RailwayNetwork()
    road = RoadwayNetwork()
    fn = FreightNetwork(rail, road)

    # cost network at current situation
    fn.cost_network()
    fn.report_to_excel("current situation")

    # cost network deriving all possible freight to railway
    fn.derive_all_to_railway()
    fn.cost_network()
    fn.report_to_excel("derive all to railway")

    # cost network deriving all freight to roadway
    fn.derive_all_to_roadway()
    fn.cost_network()
    fn.report_to_excel("derive all to roadway")


def test():
    """Gets all the reports from RailwayNetwork, in the future this will be
    addressed by methods of FreightNetwork class."""

    # initiate object
    rn = RailwayNetwork()
    road_network = RoadwayNetwork()
    fn = FreightNetwork(rn, road_network)

    # derive all road od_pairs
    fn.derive_all_to_railway()

    # rn.links_by_od_to_excel()
    rn.print_objects_report()
    road_network.report_to_excel()

    # CALCULATE SIMPLE MOBILITY COSTS and its INFRASTRUCTURE COSTS
    print "\n***********************************"
    print "Calculate simple mobility cost."
    print "***********************************"
    rn.calc_simple_mobility_cost()

    print "\n***Mobility cost results***\n"
    pprint(rn.costs["mob"])

    print "\n***Wagons results***"
    print rn.wagons

    print "\n***Locomotives results***"
    print rn.locoms

    print "\n***Global results***\n"
    print "total tons", "{:,.2f}".format(rn.get_total_tons())
    print "total ton-km", "{:,.2f}".format(rn.get_total_ton_km())
    print "average distance", rn.get_total_ton_km() / rn.get_total_tons()

    # print "\n***Idle capacity by link***"
    # for gauge in rn.links.values():
    #     for link in gauge.values():
    #         print str(link.id).ljust(10), \
    #               "{:,.1f}".format(link.idle_capacity).ljust(15), link.gauge

    # print rn.od_pairs["41-84"].has_path()

    print "\n***********************************"
    print "Calculate infrastructure cost."
    print "***********************************"
    rn.calc_infrastructure_cost()

    print "\n***infrastructure cost results***\n"
    pprint(rn.costs["inf"])

    # MAKE REPORT
    rn.report_to_excel("reports/report_simple_mobility.xlsx")

    # CALCULATE OPTIMIZED MOBILITY COSTS and its INFRASTRUCTURE COSTS
    print "\n***********************************"
    print "Calculate optimized mobility cost."
    print "***********************************"
    rn.calc_optimized_mobility_cost()

    print "\n***Mobility cost results***\n"
    pprint(rn.costs["mob"])

    print "\n***Wagons results***"
    print rn.wagons

    print "\n***Locomotives results***"
    print rn.locoms

    print "\n***Global results***\n"
    print "total tons", "{:,.2f}".format(rn.get_total_tons())
    print "total ton-km", "{:,.2f}".format(rn.get_total_ton_km())
    print "average distance", rn.get_total_ton_km() / rn.get_total_tons()

    print "\n***********************************"
    print "Calculate infrastructure cost."
    print "***********************************"
    rn.calc_infrastructure_cost()

    print "\n***infrastructure cost results***\n"
    pprint(rn.costs["inf"])

    # MAKE REPORT
    rn.report_to_excel("reports/report_optimized_mobility.xlsx")


if __name__ == '__main__':
    test()
