# -*- coding: utf-8 -*-
from modules import RailwayNetworkBuilder, RoadwayNetworkBuilder
from modules import RailwayNetworkCost, RoadwayNetworkCost
from modules import RailwayNetworkReport, RoadwayNetworkReport
from modules.builder.components.path import Path
import math
from dijkstra import find_paths
import sys

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
    RELATIVE_DENSITY_FACTOR = 2

    def __init__(self):

        self.params = {}
        self.od_pairs = {}
        self.restricted_links = {}
        self.links = {}
        self.paths = {}
        self.costs = {"mob": None, "inf": None, "time": None}
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

    def iter_links(self, limit=None, restricted=False):
        """Iterate links with an optional limit in number of results."""

        if not restricted:
            links_dict = self.links
        else:
            links_dict = self.restricted_links

        counter = 0
        for link in links_dict.values():
            for link_gauge in link.values():

                # check if limit is reached
                if limit and counter >= limit:
                    break
                counter += 1

                yield link_gauge

    # network properties
    @property
    def ton_km(self):
        """Sum all ton_km from all od_pairs used in the model."""
        total_tk_link = 0.0
        total_tk_od = 0.0

        # iterate through all links adding ton * dist
        for link in self.iter_links():
            total_tk_link += link.tons.get() * link.dist

        # iterate throught all ods adding ton * dist
        for od in self.iter_od_pairs():
            total_tk_od += od.tons.get() * od.dist

        # control that both ways of calculate total_ton_km are the same!
        msg = "Link and OD based ways of total_ton_km calculation" + \
            "differ! Link: " + str(total_tk_link) + " OD: " + \
            str(total_tk_od)
        if total_tk_od == 0:
            assert abs(total_tk_link - total_tk_od) < 0.01, msg
        elif total_tk_link > 1 and total_tk_od > 1:
            assert abs(total_tk_link / total_tk_od - 1) < 0.01, msg

        return total_tk_link

    @property
    def ton(self):
        """Sum all tons from od_pairs used in the model."""
        total_tons = 0.0

        # iterate through all od pairs adding its tons
        for od in self.iter_od_pairs():
            total_tons += od.tons.get()

        return total_tons

    @property
    def average_distance(self):
        if self.ton != 0:
            return self.ton_km / self.ton
        else:
            return 0.0

    @property
    def density(self):
        """Get average tons of density by km of network."""

        # check network dimension is not zero
        if self.dimension and self.dimension > 0:
            density = self.ton_km / self.dimension

        else:
            density = 0

        return density

    @property
    def dimension(self):
        """Calculate network dimension in km."""
        return sum([link.dist for link in self.iter_links()
                    if link.tons.get() > 0.0])

    @property
    def high_density_dimension(self):
        """Calculate network high density dimension in km."""
        high_density = self.density * self.RELATIVE_DENSITY_FACTOR
        return sum([link.dist for link in self.iter_links()
                    if link.tons.get() > high_density])

    @property
    def low_density_dimension(self):
        """Calculate network low density dimension in km."""
        low_density = self.density / self.RELATIVE_DENSITY_FACTOR
        return sum([link.dist for link in self.iter_links()
                    if link.tons.get() < low_density])

    @property
    def total_cost_tk(self):
        """Add up all the costs."""

        total_cost_tk = 0.0

        for cost_section in self.costs.values():
            if cost_section:
                for cost_name in cost_section:
                    if cost_name.startswith("total_"):
                        total_cost_tk += cost_section[cost_name]

        return total_cost_tk

    @property
    def total_cost(self):
        return self.total_cost_tk * self.ton_km

    # getters
    def get_path(self, od):

        # take id of od pair
        if type(od) == str:
            id_od = od
        else:
            id_od = od.id

        # look if path is already calculated
        if id_od in self.paths and self._use_existent_links(self.paths[id_od]):
            RV = self.paths[id_od]

        else:
            RV = self.find_shortest_path(id_od)

        return RV

    def get_path_distance(self, od):
        """Get distance of a path.

        Args:
            od: od pair wich path we are looking its distance
        """

        if od.is_intrazone():
            return 0.0
        else:
            return self.get_path(od).calc_distance(self.links)

    def get_link(self, id_link, gauge=None):
        if gauge:
            return self.links[id_link][gauge]
        else:
            return self.links[id_link]

    def remove_link(self, id_link, gauge=None):

        if gauge:
            del self.links[id_link][gauge]
        else:
            del self.links[id_link]

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

    def remove_od(self, id_od, category_od=None):

        if category_od:
            del self.od_pairs[id_od][category_od]
        else:
            del self.od_pairs[id_od]

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
            gauge = od.gauge

            # check if there are links (if the pair is not intrazone)
            if not od.is_intrazone() and od.has_operable_path():

                # find wich product categories can be regrouped with this od
                od_category = od.tons.category

                # if is regroupable, all regroupable categories can be with it
                if self.is_regroupable(od_category):
                    categories = self.get_regrouping_categories()

                # if is not regroupable, tons must go with the same category
                else:
                    categories = od_category

                # get lowest scale link of od pair, based con regrouping categ
                lowest_link_id = min(od.links,
                                     key=lambda x: self.get_link(x, gauge).tons.get(categories=categories))
                lowest_link = self.get_link(lowest_link_id, gauge)

            else:
                lowest_link = None

            # store a reference to lowest link in th od pair object
            od.set_lowest_scale_link(lowest_link)

    def find_shortest_path(self, id_od, gauge_priority=True):

        paths_network = find_paths.Network()
        paths_network.create_graphs(self.links)
        paths = paths_network.find_shortest_path(id_od)

        # select path by gauge priority
        if gauge_priority:

            if "ancha" in paths:
                path_nodes = paths["ancha"]["path"]
                gauge = "ancha"
            elif "media" in paths:
                path_nodes = paths["media"]["path"]
                gauge = "media"
            elif "angosta" in paths:
                path_nodes = paths["angosta"]["path"]
                gauge = "angosta"
            else:
                raise Exception("No path has been found for " + id_od)

        # select path by distance
        else:

            max_distance = sys.maxint
            for possible_gauge in paths:

                distance = paths[possible_gauge]["distance"]
                if distance < max_distance:
                    max_distance = distance
                    path_nodes = paths[possible_gauge]["path"]
                    gauge = possible_gauge

        path = "-".join(path_nodes)

        return Path(id_od, path, gauge)

    # booleans
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

    def is_regroupable(self, category):
        """Returns True if category can be regrouped and False otherwise."""

        if "regroup_" + str(category) in self.params:
            return self.params["regroup_" + str(category)].value == 1

        else:
            return False

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

    def links_by_od_to_excel(self, xl_links_by_od=None):
        """Write table of links by possible od pair to excel."""

        # create report object
        rep = self.REPORT_CLASS()

        # ask for excel report passing RailNetwork object itself
        rep.links_by_od_to_excel(self.paths, xl_links_by_od)

    def report_to_excel(self, xl_report=None, description=None,
                        append_report=None):
        """Make a report of modal network results in excel."""

        # create report object
        rep = self.REPORT_CLASS(xl_report, description, append_report)
        # ask for excel report passing RailNetwork object itself
        rep.report_to_excel(self)

    # PRIVATE
    def _use_existent_links(self, path):

        RV = True
        for id_link in path.links:
            if ((not id_link in self.links) or
                    (not path.gauge in self.links[id_link])):

                RV = False
                break

        return RV

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

            if od.tons.get() < 0.001:
                self.od_pairs[od.id].pop(od.tons.category)

                # check if there is any od_pair left, of another category
                if len(self.od_pairs[od.id]) == 0:
                    self.od_pairs.pop(od.id)


class RoadwayNetwork(BaseModalNetwork):

    """Represents a road network with methods to cost it.

    RoadwayNetwork() starts an empty network and it uses RoadwayNetworkBuilder
    to build an instance."""

    REPORT_CLASS = RoadwayNetworkReport
    COST_CLASS = RoadwayNetworkCost
    BUILDER_CLASS = RoadwayNetworkBuilder
    MODE_NAME = "Roadway"

    def __init__(self, builder=None, projection_factor=1.0,
                 restrictions=False):

        self.projection_factor = projection_factor
        self.restrictions = restrictions
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

    def calc_time_cost(self):
        """Calculates time cost for current mobility requirements."""
        self.costs["time"] = {"total_time": 0.0}

    def cost_network(self):
        """Cost infrastructure and mobility of the network."""

        self.calc_mobility_cost()
        self.calc_infrastructure_cost()
        self.calc_time_cost()

    def get_wagons_per_locomotive(self):
        """Dummy method to match railway interface for reporting."""
        return None

    def increase_mobility_requirements(self, od):
        pass

    def remove_mobility_requirements(self, od):
        pass

    def regroup_link(self, link):
        pass

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
    MODE_NAME = "Railway"

    def __init__(self, builder=None, projection_factor=1.0,
                 restrictions=False):

        self.projection_factor = projection_factor
        self.restrictions = restrictions
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
            self.increase_mobility_requirements(od)

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
            self.regroup_link(link)

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
        """Cost time related requirements in the railway network."""

        self.find_lowest_scale_links()
        network_cost = self.COST_CLASS(self)
        self.costs["time"] = network_cost.cost_time()

    def cost_network(self):
        """Cost infrastructure and mobility of the network.

        It uses de best cost approach (optimized mobility cost)."""

        self.calc_optimized_mobility_cost()
        self.calc_infrastructure_cost()
        self.cost_time()

    # others
    def has_railway_path(self, od):
        """Check if an od pair has an operable railway path.

        Args:
            od: od pair to be evaluated to has a railway path or not
        """

        # check if od is in paths
        try:
            self.get_path(od.id)
        except:
            return False

        # check the path is operable by railway
        path = self.paths[od.id].path
        gauge = self.paths[od.id].gauge

        has_path_and_gauge = bool(path and gauge)
        has_links = "-" in path

        return has_path_and_gauge and has_links

    def print_rolling_material_report(self):
        """Print report with rolling material results."""

        rep = self.REPORT_CLASS()
        rep.print_rolling_material_report(self)

    def get_wagons_per_locomotive(self):
        """Calculate average number of wagons per locomotive."""
        if self.locoms.running > 0.0:
            return self.wagons.running / self.locoms.running
        else:
            return 0.0

    def increase_mobility_requirements(self, od):
        """Takes an OD object and calculate its mobility requirements.

        Update the rolling material objects (wagons and locomotives) with the
        new freight service required (od pair) object and the links used by od
        pair route with the idle remaining freight transport capacity in
        locomotives.

        Args:
            od: OD pair with tons to be carried by rolling material
        """

        # check od has significant tons
        if not od.tons.get() > 0.1:
            return

        # increase material requirements and store idle capacity generated
        idle_cap_l, idle_cap_w = self._increase_rolling_material(od.tons.get(),
                                                                 od.dist)
        can_be_regrouped = self._can_od_be_regrouped(od)

        # add idle capacity of locomotives along the route used by od pair
        for id_link in od.links:
            link = self.get_link(id_link, od.gauge)

            # check that every link used by od exists in the network
            msg = "".join(("There is no link ", id_link, " and gauge ",
                           od.gauge, " for od pair ", od.id,
                           " with path: ", od.path))
            assert link, msg

            # classify idle capacity differently if can be regrouped
            if can_be_regrouped:
                link.idle_capacity_regroup += idle_cap_l
            else:
                link.idle_capacity_no_regroup += idle_cap_w

    def remove_mobility_requirements(self, od):
        """Takes an OD object and remove mobility requirements from network.

        Update the rolling material objects (wagons and locomotives) removing
        a freight service required (od pair) object and the links used by od
        pair route with the idle remaining freight transport capacity in
        locomotives.

        Args:
            od: OD pair with tons that were carried by rolling material
        """

        # check od has significant tons
        if not od.tons.get() > 0.1:
            return

        # increase material requirements and store idle capacity generated
        idle_cap_l, idle_cap_w = self._remove_rolling_material(od.tons.get(),
                                                               od.dist)
        can_be_regrouped = self._can_od_be_regrouped(od)

        # add idle capacity of locomotives along the route used by od pair
        for id_link in od.links:
            link = self.get_link(id_link, od.gauge)

            # check that every link used by od exists in the network
            msg = "".join(("There is no link ", id_link, " and gauge ",
                           od.gauge, " for od pair ", od.id,
                           " with path: ", od.path))
            assert link, msg

            # classify idle capacity differently if can be regrouped
            if can_be_regrouped:
                pass
            else:
                link.idle_capacity_no_regroup -= idle_cap_w

    # PRIVATE
    def regroup_link(self, link):

        # store current cost of network
        current_cost = self._calc_mobility_cost()["total_mobility"]

        # regroup link
        # print "regroup ", link.id
        self._regroup_link(link)

        # calculate new cost with link regrouped
        new_cost = self._calc_mobility_cost()["total_mobility"]

        if new_cost >= current_cost:
            self._revert_regroup_link(link)

    def _calc_mobility_cost(self):
        """Calculates mobility cost for current mobility requirements.

        Creates a railway NetworkCost() object to cost mobility for a network
        described by current parameters, locomotives, wagons and links data."""

        # create a railway network cost object
        network_cost = self.COST_CLASS(self)

        return network_cost.cost_mobility()

    def _increase_rolling_material(self, ton, dist):
        """Increase rolling material requirements, adding a new service.

        Args:
            ton: Tons carried in the new freight service.
            dist: Distance run by the new freight service.

        Return:
            A tuple (idle_cap_l, idle_cap_w) of idle capacity due to an
                increase in rolling material capable of manage more tons than
                needed.
            idle_cap_l: Idle capacity in locomotives.
            idle_cap_w: Idle capacity in wagons.
        """

        idle_cap_l = self.locoms.add_freight_service(ton, dist)
        idle_cap_w = self.wagons.add_freight_service(ton, dist)

        return (idle_cap_l, idle_cap_w)

    def _remove_rolling_material(self, ton, dist):
        """Remove rolling material requirements, taking out a service.

        Args:
            ton: Tons carried in the old freight service.
            dist: Distance run by the old freight service.

        Return:
            A tuple (idle_cap_l, idle_cap_w) of idle capacity that has been
                removed by taking out a service.
            idle_cap_l: Idle capacity in locomotives.
            idle_cap_w: Idle capacity in wagons.
        """

        idle_cap_l = self.locoms.remove_freight_service(ton, dist)
        idle_cap_w = self.wagons.remove_freight_service(ton, dist)

        return (idle_cap_l, idle_cap_w)

    def _can_od_be_regrouped(self, od):
        """Check if the category of an od is one that can be regrouped.

        Args:
            od: Od pair to check if it can be regrouped.
        """

        od_category = od.tons.category
        param_name = "regroup_" + str(od_category)
        if param_name in self.params:
            can_be_regrouped = bool(self.params[param_name].value)
        else:
            can_be_regrouped = True

        return can_be_regrouped

    def _regroup_link(self, link):
        """Eliminate some idleness in a link regrouping trains.

        Args:
            link: a link width idle capacity in trains to be regrouped to save
                locomotives
            idle_locs: number of idle locomotives
        """

        # calculate locomotives that can be eliminated
        idle_cap_regroup = link.idle_capacity_regroup
        loc_cap = self.params["locomotive_capacity"].value
        idle_locs = math.floor(float(idle_cap_regroup) / float(loc_cap))

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

    def _revert_regroup_link(self, link):
        """Revert previously regrouping of trains restoring idleness.

        Args:
            link: a previously regrouped link that has eliminated some idleness
            idle_locs: number of idle locomotives
        """

        # calculate locomotives that can be eliminated
        idle_cap_regroup = link.idle_capacity_regroup
        loc_cap = self.params["locomotive_capacity"].value
        idle_locs = math.floor(float(idle_cap_regroup) / float(loc_cap))

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
