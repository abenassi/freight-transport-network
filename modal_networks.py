# -*- coding: utf-8 -*-
from modules import RailwayNetworkBuilder, RoadwayNetworkBuilder
from modules import RailwayNetworkCost, RoadwayNetworkCost
from modules import RailwayNetworkReport, RoadwayNetworkReport
import math

"""
    This module is used by freight_network. It exposes classes for the two
    modal networks that compose a FreightNetwork class (RailwayNetwork and
    RoadwayNetwork).
"""


class BaseModalNetwork(object):

    """Represents a generic modal network.

    This class must be subclassed to represent a specific modal network.
    RailwayNetwork or RoadwayNetwork are modal networks.

    A freight transport modal network has origin-destination pairs that
    represent tons being carried from origin to destination. Each od pair uses
    a path wich is a sequence of links.

    The main costs of transport network are those of mobility and
    infrastructure. Subclassed modal networks provide methods to cost mobility
    (attached mainly to od pairs characteristics) and infrastructure
    (attached mainly to links characteristics).

    A modal network has 5 main data members:
        1. params: parameters of the network used in calculations
        2. od_pairs: od_pairs using the network
        3. links: links available to od pair paths
        4. paths: paths for all possible od pairs in the network
        5. costs: mobility and infrastructure costs of the network
    """

    def __init__(self):

        self.params = {}
        self.od_pairs = {}
        self.links = {}
        self.paths = {}
        self.costs = {"mob": None, "inf": None}
        self.is_simple_costed = False

    def __iter__(self):
        return self.iter_links()

    # PUBLIC
    # iters
    def iter_od_pairs(self, limit=None):
        """Iterate od pairs with an optional limit in number of results."""

        counter = 0
        for od_pair in self.od_pairs.values():
            for od_pair_category in od_pair.values():

                # check if limit is reached
                if limit and counter >= limit:
                    break
                counter += 1

                yield od_pair_category

    def iter_links(self, limit=None):
        """Iterate links with an optional limit in number of results."""

        counter = 0
        for link in self.links.values():
            for link_gauge in link.values():

                # check if limit is reached
                if limit and counter >= limit:
                    break
                counter += 1

                yield link_gauge

    # getters
    def get_path(self, od):
        return self.paths[od.get_id()]

    def get_path_distance(self, od):
        """Get distance of a path.

        Args:
            od: od pair wich path we are looking its distance
        """

        if od.is_intrazone():
            return 0.0
        else:
            return self.get_path(od).calc_distance(self.get_links())

    def get_paths(self):
        return self.paths

    def get_links(self):
        return self.links

    def get_link(self, id_link, gauge=None):
        if gauge:
            return self.links[id_link][gauge]
        else:
            return self.links[id_link]

    def get_od(self, id_od, category_od):
        """Returns existent od pair or create a new one if it doesn't exist.

        Args:
            id_od: the origin-destination id (eg. "1-3")
            category_od: the railway category of the freight transported.
        """

        # check if od pair is in the network
        if id_od not in self.od_pairs:
            self._create_od_pair(id_od, category_od)

        # check if od pair has the category asked
        if category_od not in self.od_pairs[id_od]:
            self._create_od_pair(id_od, category_od)

        return self.od_pairs[id_od][category_od]

    def has_od(self, id_od, category_od):
        """Returns true if od pair exists in the network.

        Args:
            id_od: the origin-destination id (eg. "1-3")
            category_od: the railway category of the freight transported.
        """

        # check if od pair is in the network
        if (id_od in self.od_pairs) and (category_od in self.od_pairs[id_od]):
            has_od = True
        else:
            has_od = False

        return has_od

    def has_od_pairs(self):
        return len(self.od_pairs) > 0

    def get_total_ton_km(self):
        """Sum all ton_km from all od_pairs used in the model."""
        total_tk_link = 0.0
        total_tk_od = 0.0

        # iterate through all links adding ton * dist
        for link in self.links.values():
            for link_gauge in link.values():
                total_tk_link += link_gauge.get_ton() * link_gauge.get_dist()

        # iterate throught all ods adding ton * dist
        for od in self.iter_od_pairs():
            total_tk_od += od.get_ton() * od.get_dist()

        # control that both ways of calculate total_ton_km are the same!
        msg = "Link and OD based ways of total_ton_km calculation" + \
            "differ! Link: " + str(total_tk_link) + " OD: " + \
            str(total_tk_od)
        if total_tk_od == 0:
            assert abs(total_tk_link - total_tk_od) < 0.01, msg
        elif total_tk_link > 1 and total_tk_od > 1:
            assert abs(total_tk_link / total_tk_od - 1) < 0.01, msg

        return total_tk_link

    def get_total_tons(self):
        """Sum all tons from od_pairs used in the model."""
        total_tons = 0.0

        # iterate through all od pairs adding its tons
        for od in self.iter_od_pairs():
            total_tons += od.get_ton()

        return total_tons

    def get_average_distance(self):
        if self.get_total_tons() != 0:
            return self.get_total_ton_km() / self.get_total_tons()
        else:
            return 0.0

    def get_dimensions(self):
        """Calculate network dimensions in km.

        Returns:
            dimensions = {"total": total dimension,
                          "high": high_density dimension,
                          "low": low_density dimension}
        """
        # calculate total dimension
        total_dimension = sum([link.get_dist() for link in self.iter_links()
                               if link.get_ton() > 0.0])

        # calculate average density
        if total_dimension > 0.1:
            average_density = self.get_total_ton_km() / total_dimension
        else:
            average_density = 0.0

        # calculate high density dimension
        high_density = average_density * 2
        high_dimension = sum([link.get_dist() for link in self.iter_links()
                              if link.get_ton() > high_density])

        # calculate low density dimension
        low_density = average_density * 2
        low_dimension = sum([link.get_dist() for link in self.iter_links()
                             if link.get_ton() < low_density])

        dimensions = {"total": total_dimension,
                      "high": high_dimension,
                      "low": low_dimension}

        return dimensions

    def get_costs_tk(self):
        return self.costs

    def get_total_cost_tk(self):
        """Add up all the costs."""

        total_cost_tk = 0.0

        for cost_section in self.costs.values():
            for cost_name in cost_section:
                if cost_name.startswith("total_"):
                    total_cost_tk += cost_section[cost_name]

        return total_cost_tk

    def get_total_cost(self):
        return self.get_total_cost_tk() * self.get_total_ton_km()

    def is_regroupable(self, category):
        """Returns True if category can be regrouped and False otherwise."""

        if "regroup_" + str(category) in self.params:
            return self.params["regroup_" + str(category)].value == 1

        else:
            return False

    def get_regrouping_categories(self):
        """Return a list with all the categories that can be regrouped."""

        regrouping_categories = []

        # iter regrouping categories in parameters dictionary
        category = 1
        regroup_prefix = "regroup_"
        while regroup_prefix + str(category) in self.params:

            # add regrouping categories to the list
            if self.params[regroup_prefix + str(category)].value == 1:
                regrouping_categories.append(category)

            category += 1

        return regrouping_categories

    def find_lowest_scale_links(self):
        """Find the lowest scale link used by every od pair."""

        # iterate od pairs of the network
        for od in self.iter_od_pairs():

            # get the gauge of the link
            gauge = od.get_gauge()

            # check if there are links (if the pair is not intrazone)
            if not od.is_intrazone() and od.has_operable_path():

                # find wich product categories can be regrouped with this od
                od_category = od.get_category()

                # if is regroupable, all regroupable categories can be with it
                if self.is_regroupable(od_category):
                    categories = self.get_regrouping_categories()

                # if is not regroupable, tons must go with the same category
                else:
                    categories = od_category

                # get lowest scale link of od pair, based con regrouping categ
                lowest_link_id = min(od.get_links(),
                                     key=lambda x: self.get_link(x, gauge).get_ton(categories=categories))
                lowest_link = self.get_link(lowest_link_id, gauge)

            else:
                lowest_link = None

            # store a reference to lowest link in th od pair object
            od.set_lowest_scale_link(lowest_link)

    def is_main_track(self, gross_tk, dist):
        """Check if this is a main track.

        If net tons density (ton-km/km) goes below a certain threshold, this is
        a secondary track. If density goes above the threshold, is a main
        track."""

        # store parameters in short-name variables
        net_to_gross = self.params["net_to_gross_factor"].value
        main_min_density = self.params["main_min_density"].value

        # calculate net ton-km
        net_tk = gross_tk / net_to_gross

        # calculate density
        density = net_tk / dist

        return density > main_min_density

    # reports
    def print_objects_report(self):
        """Print report with examples of objects inside RailwayNetwork."""

        rep = self.REPORT_CLASS()
        rep.print_objects_report(self)

    def print_global_results_report(self):
        """Print report with only global results."""

        rep = self.REPORT_CLASS()
        rep.print_global_results_report(self)

    def print_costs_report(self):
        """Print report with mobility and infrastructure costs report."""

        rep = self.REPORT_CLASS()
        rep.print_costs_report(self)

    def report_to_excel(self, xl_report=None, description=None,
                        append_report=None):
        """Make a report of modal network results in excel."""

        # create report object
        rep = self.REPORT_CLASS(xl_report, description, append_report)
        # ask for excel report passing RailNetwork object itself
        rep.report_to_excel(self)

    def links_by_od_to_excel(self, xl_links_by_od=None):
        """Write table of links by possible od pair to excel."""

        # create report object
        rep = self.REPORT_CLASS()

        # ask for excel report passing RailNetwork object itself
        rep.links_by_od_to_excel(self.get_paths(), xl_links_by_od)

    # PRIVATE
    def _create_od_pair(self, id_od, category_od):
        network_builder = self.BUILDER_CLASS()
        network_builder.create_od_pair(self, id_od, category_od)

    def _reset_links(self):
        for link in self.iter_links():
            link.reset()

    def _clean_od_pairs(self):
        """Remove od_pairs with no tons."""

        # iterate od pairs looking for empty ones (ie, with no tons)
        for od in self.iter_od_pairs():

            if od.get_ton() < 0.001:
                self.od_pairs[od.get_id()].pop(od.get_category())

                # check if there is any od_pair left, of another category
                if len(self.od_pairs[od.get_id()]) == 0:
                    self.od_pairs.pop(od.get_id())


class RoadwayNetwork(BaseModalNetwork):

    """Represents a road network with methods to cost it.

    RoadwayNetwork() starts an empty network and it uses RoadwayNetworkBuilder
    to build an instance."""

    REPORT_CLASS = RoadwayNetworkReport
    COST_CLASS = RoadwayNetworkCost
    BUILDER_CLASS = RoadwayNetworkBuilder

    def __init__(self, builder=None):

        self.trucks = None
        super(RoadwayNetwork, self).__init__()

        # check if network was constructed with a specified builder
        if builder:
            network_builder = builder
        else:
            network_builder = self.BUILDER_CLASS()

        # build network
        network_builder.build(self)

    # PUBLIC
    # cost calculations
    def calc_mobility_cost(self):
        """Calculates mobility cost."""

        # reset network before calculate costs
        self._reset_network()

        # calculate and store mobility costs for all mobility requirements
        network_cost = self.COST_CLASS(self)
        self.costs["mob"] = network_cost.cost_mobility()

    def calc_infrastructure_cost(self):
        """Calculates infrastructure cost for current mobility requirements."""

        # create a railway network cost object
        network_cost = self.COST_CLASS(self)

        # calculate and store infrastructure costs
        self.costs["inf"] = network_cost.cost_infrast()

    def cost_network(self):
        """Cost infrastructure and mobility of the network."""

        self.calc_mobility_cost()

        self.calc_infrastructure_cost()


    # PRIVATE
    def _reset_network(self):
        self._reset_links()
        self._clean_od_pairs()


class RailwayNetwork(BaseModalNetwork):

    """Represents a rail network with methods to cost it.

    RailwayNetwork() starts an empty network and it uses RailwayNetworkBuilder
    to build an instance.
    """

    REPORT_CLASS = RailwayNetworkReport
    COST_CLASS = RailwayNetworkCost
    BUILDER_CLASS = RailwayNetworkBuilder

    def __init__(self, builder=None):

        self.wagons = None
        self.locoms = None
        super(RailwayNetwork, self).__init__()

        # check if network was constructed with a specified builder
        if builder:
            network_builder = builder
        else:
            network_builder = self.BUILDER_CLASS()

        # build network
        network_builder.build(self)

    # PUBLIC
    # cost calculations
    def calc_mobility_requirements(self):
        """Calculate mobility requirements of running each origin-destination
        rail service independently."""

        # iterate through all od pairs
        for od in self.iter_od_pairs():

            # calculate mobility requirements to run rail service for od
            self._calculate_mobility_od(od)

    def calc_simple_mobility_cost(self):
        """Calculates mobility cost of running each origin-destination rail
        service independently."""

        # reset network before calculate costs
        self._reset_network()

        # calculate mobility requirements to run all rail services
        self.calc_mobility_requirements()

        # calculate and store mobility costs for all mobility requirements
        self.costs["mob"] = self._calc_mobility_cost()

        self.is_simple_costed = True

    def calc_optimized_mobility_cost(self):
        """Regroup trains operating below maximum capacity.

        Check if regrouping trains in a single link is more cost-effective than
        previous situation, where some trains where operating below their
        maximum capacity. If its not the case, revert regrouping."""

        # check that simple cost mobility was calculated
        if not self.is_simple_costed:
            self.calc_simple_mobility_cost()

        # iterate through all links
        for link in self.iter_links():

            # store current cost of network
            current_cost = self._calc_mobility_cost()["total_mobility"]

            # calculate locomotives that can be eliminated
            idle_cap_regroup = link.get_idle_cap_regroup()
            loc_cap = self.params["locomotive_capacity"].value
            idle_locs = math.floor(float(idle_cap_regroup) / float(loc_cap))

            # regroup link
            # print "regroup ", link.get_id()
            self._regroup_link(link, idle_locs)

            # calculate new cost with link regrouped
            new_cost = self._calc_mobility_cost()["total_mobility"]

            # if new cost is not lower, revert regroup of link
            # if False:
            if new_cost >= current_cost:
                # print "new cost:", new_cost, "current cost:", current_cost
                # print "revert ", link.get_id()
                self._revert_regroup_link(link, idle_locs)

        # calculate and store mobility costs
        self.costs["mob"] = self._calc_mobility_cost()

        # now network is not simple costed anymore (is optimized costed)
        self.is_simple_costed = False

    def calc_infrastructure_cost(self):
        """Calculates infrastructure cost for current mobility requirements.

        Creates a railway NetworkCost() object to cost infrastructure for a
        network described by current parameters, locomotives, wagons and
        links data."""

        # create a railway network cost object
        network_cost = self.COST_CLASS(self)

        # calculate and store infrastructure costs
        self.costs["inf"] = network_cost.cost_infrast()

    def cost_time(self):

        # create a railway network cost object
        network_cost = self.COST_CLASS(self)

        # calculate and store time costs
        self.costs["time"] = network_cost.cost_time()

    def cost_network(self):
        """Cost infrastructure and mobility of the network.

        It uses de best cost approach (optimized mobility cost)."""

        # self.calc_optimized_mobility_cost()
        self.calc_simple_mobility_cost()
        self.calc_infrastructure_cost()
        self.cost_time()

    # others
    def has_railway_path(self, od):
        """Check if an od pair has an operable railway path.

        Args:
            od: od pair to be evaluated to has a railway path or not
        """

        # check if od is in paths
        if not od.get_id() in self.paths:
            return False

        # check the path is operable by railway
        path = self.paths[od.get_id()].get_path()
        gauge = self.paths[od.get_id()].get_gauge()

        has_path_and_gauge = bool(path and gauge)
        has_links = "-" in path

        return has_path_and_gauge and has_links

    def print_rolling_material_report(self):
        """Print report with rolling material results."""

        rep = self.REPORT_CLASS()
        rep.print_rolling_material_report(self)

    # PRIVATE
    def _calc_mobility_cost(self):
        """Calculates mobility cost for current mobility requirements.

        Creates a railway NetworkCost() object to cost mobility for a network
        described by current parameters, locomotives, wagons and links data."""

        # create a railway network cost object
        network_cost = self.COST_CLASS(self)

        return network_cost.cost_mobility()

    def _calculate_mobility_od(self, od):
        """Takes an OD object and calculate its mobility requirements.

        Update the rolling material objects (wagons and locomotives) with the
        new freight service required (od pair) object and the links used by od
        pair route with the idle remaining freight transport capacity in
        locomotives.

        Args:
            od: OD pair with tons to be carried by rolling material
        """

        # check od has significant tons
        if not od.get_ton() > 0.1:
            return

        # wagons mobility
        self.wagons.add_freight_service(od.get_ton(), od.get_dist())

        # locomotives mobility
        idle_capacity_l = self.locoms.add_freight_service(od.get_ton(),
                                                          od.get_dist())

        # check if od can be regroup or not (to remove idle capacity)
        od_category = od.get_category()
        param_name = "regroup_" + str(od_category)
        if param_name in self.params:
            can_be_regrouped = bool(self.params[param_name].value)
        else:
            can_be_regrouped = True

        # add idle capacity of locomotives along the route used by od pair
        exception_counter = 0
        MAX_EXCEPTIONS = 50
        for id_link in od.get_links():

            assert exception_counter < MAX_EXCEPTIONS, "Too many error paths."

            link = self.get_link(id_link, od.gauge)

            # try to update tons and idle capacity of link-gauge
            try:
                if can_be_regrouped:
                    link.add_idle_cap_regroup(idle_capacity_l)
                else:
                    link.add_idle_cap_no_regroup(idle_capacity_l)

            # if impossible, there is no link-gauge in the network for od_pair
            except:
                exception_counter += 1
                print "".join(("There is no link ", id_link, " and gauge ",
                               od.get_gauge(), " for od pair ", od.get_id(),
                               " with path: ", od.get_path()))

    def _regroup_link(self, link, idle_locs):
        """Eliminate some idleness in a link regrouping trains.

        Args:
            link: a link width idle capacity in trains to be regrouped to save
                locomotives
            idle_locs: number of idle locomotives
        """

        # store parameters to be used in short variables
        loc_capacity = self.params["locomotive_capacity"].value
        wagon_capacity = self.params["wagon_capacity"].value

        # calcualte wagons regrouped
        wagons_regrouped = idle_locs * loc_capacity / wagon_capacity

        # update idle_capacity of link
        link.regroup(idle_locs * loc_capacity)

        # update rolling material time requirements
        self.locoms.regroup(idle_locs, link.get_dist())
        self.wagons.add_regroup_time(wagons_regrouped)

    def _revert_regroup_link(self, link, idle_locs):
        """Revert previously regrouping of trains restoring idleness.

        Args:
            link: a previously regrouped link that has eliminated some idleness
            idle_locs: number of idle locomotives
        """

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

    def _reset_network(self):
        self.wagons.reset()
        self.locoms.reset()
        self._reset_links()
        self._clean_od_pairs()
        self.is_simple_costed = False


def test_railway_network():

    # initiate object
    rail_network = RailwayNetwork()
    description = "situacion base"

    # print firsts reports, without costs calculations
    # rail_network.links_by_od_to_excel()
    rail_network.print_objects_report()


    # CALCULATE SIMPLE MOBILITY COSTS and its INFRASTRUCTURE COSTS
    print "\n***********************************"
    print "Calculate simple mobility cost."
    print "***********************************"
    rail_network.calc_simple_mobility_cost()
    rail_network.print_rolling_material_report()
    rail_network.print_global_results_report()

    print "\n***********************************"
    print "Calculate infrastructure cost."
    print "***********************************"
    rail_network.calc_infrastructure_cost()
    rail_network.print_costs_report()

    # MAKE EXCEL COMPLETE REPORT
    rail_network.report_to_excel("reports/railway_report.xlsx",
                                 description + " - sin reagrupamiento",
                                 append_report=False)


    # CALCULATE OPTIMIZED MOBILITY COSTS and its INFRASTRUCTURE COSTS
    print "\n***********************************"
    print "Calculate optimized mobility cost."
    print "***********************************"
    rail_network.calc_optimized_mobility_cost()
    rail_network.print_rolling_material_report()
    rail_network.print_global_results_report()

    print "\n***********************************"
    print "Calculate infrastructure cost."
    print "***********************************"
    rail_network.calc_infrastructure_cost()
    rail_network.print_costs_report()

    # MAKE EXCEL COMPLETE REPORT
    rail_network.report_to_excel("reports/railway_report.xlsx",
                                 description + " - con reagrupamiento",
                                 append_report=True)


def test_roadway_network():

    roadway_network = RoadwayNetwork()
    roadway_network.print_objects_report()
    roadway_network.print_global_results_report()


if __name__ == '__main__':

    print "\n*****MANUAL TEST OF RAILWAY NETWORK*****\n"
    test_railway_network()

    # print "\n*****MANUAL TEST OF ROADWAY NETWORK*****\n"
    # test_roadway_network()
