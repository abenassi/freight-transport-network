# -*- coding: utf-8 -*-
from modules import RailwayNetworkBuilder, RailwayNetworkCost, RailwayReport
from pprint import pprint
import math
import numpy as np


class RailwayNetwork():

    """Represents a rail network with methods to cost it.

    RailwayNetwork() starts an empty network. It needs to be fed with the
    following data:
        1. parameters: used in calculations
        2. od_pairs: od_pairs data from road network to be derived
        3. od_paris_current: od_pairs currently being transported by train
        4. links: a list of links
        5. paths: a list of paths assigned to each od_pair

    It uses RailwayNetworkBuilder to build an instance.
    """

    def __init__(self):

        self.params = {}
        self.od_pairs = {}
        self.od_pairs_current = {}
        self.od_pairs_rejected = {}
        self.links = {}
        self.paths = {}
        self.wagons = None
        self.locoms = None
        self.costs = {"mob": None, "inf": None}

        # build railway network
        rnb = RailwayNetworkBuilder()
        rnb.build_railway_network(self)

    # PUBLIC
    def calc_simple_mobility_cost(self):
        """Calculates mobility cost of running each origin-destination rail
        service independently."""

        # iterate through all od pairs
        for od in self.od_pairs.values():

            # check if od_pair is derivable
            if self._od_pair_is_derivable(od):

                # calculate how much tons of od will be derived
                self._calculate_derived_tons(od)

                # calculate mobility requirements to run rail service for od
                self._calculate_mobility_od(od)

            # if its not derivable, go to rejected od dictionary
            else:
                # add it to od_paris rejected dictionary
                self.od_pairs_rejected[od.id] = od

                # delete it from od_pairs dictionary
                del self.od_pairs[od.id]

        # add all od pairs that are currently being carried by railway
        for od_current in self.od_pairs_current.values():

                # calculate mobility requirements to run rail service for od
                self._calculate_mobility_od(od_current)

        # calculate and store mobility costs for all mobility requirements
        self.costs["mob"] = self._calc_mobility_cost()

    def calc_optimized_mobility_cost(self):
        """Regroup trains operating below maximum capacity.

        Check if regrouping trains in a single link is more cost-effective than
        previous situation, where some trains where operating below their
        maximum capacity. If its not the case, revert regrouping."""

        # iterate through all links
        for link in self.links.values():
            for link_gauge in link.values():

                # store current cost of network
                current_cost = self._calc_mobility_cost()["total_mobility"]

                # calculate locomotives that can be eliminated
                idle_capacity = link_gauge.idle_capacity
                loc_capacity = self.params["locomotive_capacity"].value
                idle_locs = math.floor(float(idle_capacity) /
                                       float(loc_capacity))

                # regroup link
                self._regroup_link(link_gauge, idle_locs)

                # calculate new cost with link regrouped
                new_cost = self._calc_mobility_cost()["total_mobility"]

                # if new cost is not lower, revert regroup of link
                # if False:
                if new_cost >= current_cost:
                    self._revert_regroup_link(link_gauge, idle_locs)

        # calculate and store mobility costs
        self.costs["mob"] = self._calc_mobility_cost()

    def calc_infrastructure_cost(self):
        """Calculate infrastructure costs."""

        # calculate and store infrastructure costs
        self.costs["inf"] = self._calc_infrastructure_cost()

    # GET methods
    def get_rejected_tons(self):
        """Sum all rejected tons from od_pairs_rejected."""

        rejected_tons = 0.0

        # iterate through all rejected od pairs adding its tons
        for od in self.od_pairs_rejected.values():
            rejected_tons += od.ton

        return rejected_tons

    def get_total_tons(self):
        """Sum all tons from od_pairs used in the model."""
        total_tons = 0.0

        # iterate through all od pairs adding its tons
        for od in self.od_pairs.values():
            total_tons += od.ton

        return total_tons

    def get_total_ton_km(self):
        """Sum all ton_km from all od_pairs used in the model."""
        total_ton_km = 0.0

        # iterate through all links adding ton * dist
        for link in self.links.values():
            for link_gauge in link.values():

                total_ton_km += link_gauge.ton * link_gauge.dist

        return total_ton_km

    # REPORT methods
    def report_to_excel(self, xl_report=None):
        """Make a report of RailwayNetwork results in excel."""

        # create report object
        rep = RailwayReport(xl_report)

        # ask for excel report passing RailNetwork object itself
        rep.report_to_excel(self)

    def print_objects_report(self):
        """Print report with examples of objects inside RailwayNetwork."""

        # create report object
        rep = RailwayReport()

        # ask for excel report passing RailNetwork object itself
        rep.print_objects_report(self)

    def print_costs_report(self):
        """Print only costs report of RailwayNetwork."""

        # create report object
        rep = Report()

        # ask for excel report passing RailNetwork object itself
        rep.print_complete_report(self)

    # PRIVATE
    def _calc_infrastructure_cost(self):
        """Calculates infrastructure cost for current mobility requirements.

        Creates a railway NetworkCost() object to cost infrastructure for a
        network described by current parameters, locomotives, wagons and
        links data."""

        # create a railway network cost object
        network_cost = RailwayNetworkCost(self.params, self.locoms,
                                          self.wagons, self.links)

        return network_cost.cost_infrast()

    def _calc_mobility_cost(self):
        """Calculates mobility cost for current mobility requirements.

        Creates a railway NetworkCost() object to cost mobility for a network
        described by current parameters, locomotives, wagons and links data."""

        # create a railway network cost object
        network_cost = RailwayNetworkCost(self.params, self.locoms,
                                          self.wagons, self.links)

        return network_cost.cost_mobility()

    def _calculate_mobility_od(self, od):
        """Takes an OD object and calculate its mobility operating requirements.

        Update the rolling material objects (wagons and locomotives) with the
        new freight service required (od pair) object and the links used by od
        pair route with the idle remaining freight transport capacity in
        locomotives."""

        # wagons mobility
        idle_capacity_w = self.wagons.add_freight_service(od.ton, od.dist)

        # locomotives mobility
        idle_capacity_l = self.locoms.add_freight_service(od.ton, od.dist)

        # add idle capacity of locomotives along the route used by od pair
        for link in od.links:

            # try to update tons and idle capacity of link-gauge
            try:
                self.links[link][od.gauge].add_ton(od.ton)
                self.links[link][od.gauge].add_idle_cap(idle_capacity_l)

            # if impossible, there is no link-gauge in the network for od_pair
            except:
                print "".join(("There is no link ", link, " and gauge ",
                               od.gauge, " for od pair ", od.id, " with path: ",
                               od.path))

    def _regroup_link(self, link, idle_locs):
        """Takes freight idleness situation in a link (extra capacity to
        transport freight in the link that is not being used) and test the
        convenience of regroup trains to minimize idleness."""

        # store parameters to be used in short variables
        loc_capacity = self.params["locomotive_capacity"].value
        wagon_capacity = self.params["wagon_capacity"].value

        # calcualte wagons regrouped
        wagons_regrouped = idle_locs * loc_capacity / wagon_capacity

        # update idle_capacity of link
        link.regroup(idle_locs * loc_capacity)

        # update rolling material time requirements
        self.locoms.regroup(idle_locs, link.dist)
        self.wagons.add_regroup_time(wagons_regrouped)

    def _revert_regroup_link(self, link, idle_locs):
        """Takes freight idleness situation in a link (extra capacity to
        transport freight in the link that is not being used) and test the
        convenience of regroup trains to minimize idleness."""

        # store parameters to be used in short variables
        loc_capacity = self.params["locomotive_capacity"].value
        wagon_capacity = self.params["wagon_capacity"].value

        # calcualte wagons regrouped
        wagons_regrouped = idle_locs * loc_capacity / wagon_capacity

        # update idle_capacity of link
        link.revert_regroup(idle_locs * loc_capacity)

        # update rolling material time requirements
        self.locoms.revert_regroup(idle_locs, link.dist)
        self.wagons.subtract_regroup_time(wagons_regrouped)

    def _od_pair_is_derivable(self, od):
        """Indicate if od pair is derivable or not."""

        # check if ther is an operable railway path for the od pair
        has_railway_path = od.has_railway_path()

        # check if od pair meet minimum tons adn distance to be derivable
        min_ton = od.ton > self.params["min_tons_to_derive"].value
        min_dist = od.dist > self.params["min_dist_to_derive"].value

        return min_ton and min_dist and has_railway_path

    def _get_derivation_coefficient(self, od):

        # assign parameters to short variables
        max_dist = float(self.params["dist_of_max_derivation"].value)
        min_dist = float(self.params["min_dist_to_derive"].value)
        max_tons = float(self.params["tons_of_max_derivation"].value)
        min_tons = float(self.params["min_tons_to_derive"].value)
        max_deriv = float(self.params["max_derivation"].value)

        # assign max derivation if distance and tons are greater than max
        if od.dist >= max_dist and od.ton >= max_tons:
            deriv_coefficient = max_deriv

        # assign zero derivation if distance and tons are lower than min
        elif od.dist <= min_dist and od.ton >= min_tons:
            deriv_coefficient = 0.0

        # interpolate derivation coefficient otherwise
        else:

            # calculate substitution coefficient for tons / dist
            coef_ton_dist = (max_tons - min_tons) / (max_dist - min_dist)

            # get tons and distance relevant to interpolate
            # if one of the two dimensions exceeds maximum, maximum will be
            # used
            tons = min(od.ton, max_tons)
            dist = min(od.dist, max_dist)

            # transform dist in tons unit wiht substitution coefficient
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

    def _calculate_derived_tons(self, od):
        """Calculate derivable tons and modify OD tons accordingly."""

        # calculate coefficient of tons to be derived
        coeff = self._get_derivation_coefficient(od)

        # modify od tons to be derived
        od.ton = od.ton * coeff


def main():

    # initiate object
    rn = RailwayNetwork()
    rn.print_objects_report()

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
    print "rejected tons", "{:,.2f}".format(rn.get_rejected_tons())

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
    print "rejected tons", "{:,.2f}".format(rn.get_rejected_tons())

    print "\n***********************************"
    print "Calculate infrastructure cost."
    print "***********************************"
    rn.calc_infrastructure_cost()

    print "\n***infrastructure cost results***\n"
    pprint(rn.costs["inf"])

    # MAKE REPORT
    rn.report_to_excel("reports/report_optimized_mobility.xlsx")


if __name__ == '__main__':
    main()
