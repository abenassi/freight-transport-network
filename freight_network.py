from modal_networks import RailwayNetwork, RoadwayNetwork
import numpy as np
from optimization import WeakLinksAggregator, WeakOdsAggregator
from optimization import LinksTrafficRerouter
from modules import BaseReport

"""
    This is the main module that will be visible to the user. Exposes
    FreightNetwork class with methods to derive traffic between freight
    transport modal networks and to cost the overall network. It will be able
    to try different traffic configurations to find the one with lowest
    overall cost.
"""


class ReroutingMethods(object):
    """Rerouting methods to be inherited by FreightNetwork.

    This class is used just to separate a bunch of strongly related methods
    used by FreightNetwork class."""

    def __init__(self, freight_network):
        self.fn = freight_network

    def reroute_link(self, id_rail_link, gauge_rail_link, allow_original=True):
        """Reroute all ods using a railway link or derive to roadway."""

        # list to store road od pairs receiving derivated freight
        road_od_derivations = []

        # list to store rerouted od pairs
        rerouted_ods = []

        # get rail link from the rail network
        rail_link = self.fn.rail.get_link(id_rail_link, gauge_rail_link)

        for rail_od in self.fn.rail.iter_od_pairs():

            use_rail_link = rail_link.id in rail_od.links
            use_same_gauge = rail_link.gauge == rail_od.gauge
            if use_rail_link and use_same_gauge:

                succeed = self.reroute_od(self.fn.rail, rail_od, rail_link)

                if not succeed:
                    # derive rail tons to roadway
                    COEFF = 1.0
                    road_od_derivation = self.od_to_roadway(rail_od, COEFF,
                                                            allow_original)

                    # store reference to road od pair derivation for reversion
                    road_od_derivations.append(road_od_derivation)

                else:
                    rerouted_ods.append(rail_od)

        return rerouted_ods, road_od_derivations

    def reroute_od(self, modal_network, od, link):
        """Change path of od to avoid using link."""

        new_path = modal_network.find_shortest_path(od.id,
                                                    restrictions=[link.id])

        if new_path:
            sef._update_links_tons(new_path, od)
            od.set_path(new_path.path, od.gauge)
            succeed = True

        else:
            succeed = False

        return succeed

    def revert_reroute_od(self, modal_network, od):
        """Restore original path of od."""

        original_path = modal_network.get_path(od)

        assert bool(original_path) = True, "No original path could be found."

        sef._update_links_tons(original_path, od)

        od.set_path(original_path.path, od.gauge)

    # PRIVATE
    def _update_links_tons(self, new_path, od):
        """Move tons from old_links to new_links."""

        old_links = od.links
        new_links = new_path.links

        original_ton = od.tons.get_original()
        derived_ton = od.tons.get_derived()

        # remove tons from modal_network old_links used by od
        for old_id_link in old_links:
            if old_id_link not in new_links:
                old_link = modal_network.get_link(old_id_link, od.gauge)
                old_link.tons.remove_original(ton=original_ton,
                                              categories=od.category,
                                              id_ods=od.id)
                old_link.tons.remove_derived(ton=original_ton,
                                             categories=od.category,
                                             id_ods=od.id)

        # add derived tons to modal_network new_links, used by the new path
        for new_id_link in new_links:
            if new_id_link not in new_links:
                new_link = modal_network.get_link(new_id_link, od.gauge)
                new_link.tons.add_original(ton=original_ton,
                                           categories=od.category,
                                           id_ods=od.id)
                new_link.tons.add_derived(ton=original_ton,
                                          categories=od.category,
                                          id_ods=od.id)

class DerivationMethods(object):

    """Railway/Roadway derivation methods to be inherited by FreightNetwork.

    This class is used just to separate a bunch of strongly related methods
    used by FreightNetwork class."""

    def __init__(self, freight_network):
        self.fn = freight_network

    # PUBLIC
    def all_to_railway(self):
        """Derive all possible road od pairs from road mode to rail mode."""

        # iterate road od_pairs
        for road_od in self.fn.road.iter_od_pairs():

            # check if od_pair is derivable
            if self._road_od_pair_is_derivable(road_od):

                # derive road tons to railway
                self.od_to_railway(road_od, allow_original=True)

        # find lowest scale link for each od pair of the networks
        self.fn.rail.find_lowest_scale_links()
        self.fn.road.find_lowest_scale_links()

    def all_to_roadway(self):
        """Derive all possible rail od pairs from rail mode to road mode."""

        # iterate road od_pairs
        for rail_od in self.fn.rail.iter_od_pairs():

            # derive road tons to railway
            COEFF = 1.0
            self.od_to_roadway(rail_od, COEFF, allow_original=True)

        # find lowest scale link for each od pair of the networks
        self.fn.rail.find_lowest_scale_links()
        self.fn.road.find_lowest_scale_links()

    def od_to_railway(self, road_od, coeff=None, allow_original=True):
        """Derive a road od pair to railway mode.

        Args:
            road_od: Road OD pair to be derived.
            coeff: Percentage of tons to be derived.
        """

        # get od pair caracteristics and rail od pair that will receive freight
        id_od = road_od.id
        category = road_od.tons.category
        rail_od = self.fn.rail.get_od(id_od, category)

        # get tons that have already been derived to rail
        ton_derived = rail_od.tons.get_derived()
        ton_derivable = road_od.tons.get_original()

        # assign default value if none coeff is passed
        if not coeff:
            od_scale = ton_derived + ton_derivable
            od_road_dist = road_od.dist
            coeff = self._get_derivation_coefficient(od_scale, od_road_dist,
                                                     category)

        # derive road_od pair to a rail_od pair
        self._derive_od(road_od, rail_od, coeff,
                        self.fn.road, self.fn.rail,
                        allow_original)

        # returns rail_od for eventual reversion
        return rail_od

    def od_to_roadway(self, rail_od, coeff=None, allow_original=False):
        """Derive a rail od pair to roadway mode.

        Args:
            rail_od: Rail OD pair to be derived.
            coeff: Percentage of tons to be derived.
        """

        # get od pair caracteristics and rail od pair that will receive freight
        id_od = rail_od.id
        category = rail_od.tons.category
        road_od = self.fn.road.get_od(id_od, category)

        # assign default value if none coeff is passed
        if not coeff:
            coeff = 1.0

        # derive rail_od pair to a road_od pair
        self._derive_od(rail_od, road_od, coeff,
                        self.fn.rail, self.fn.road,
                        allow_original)

        # returns road_od pair for eventual reversion
        return road_od

    def link_to_railway(self, id_road_link, gauge_road_link,
                        allow_original=True):
        """Derive all possible road od pairs that use road_link to rail."""

        # list to store rail od pairs receiving derivated freight
        rail_od_derivations = []

        # get road link from the road network
        road_link = self.fn.road.get_link(id_road_link, gauge_road_link)

        for road_od in self.fn.road.iter_od_pairs():

            use_road_link = road_link.id in road_od.links
            use_same_gauge = road_link.gauge == road_od.gauge
            is_derivable = self._road_od_pair_is_derivable(road_od)
            if use_road_link and use_same_gauge and is_derivable:

                # calculate proportion of tons to be derived
                rail_od = self.fn.rail.get_od(road_od.id,
                                              road_od.tons.category)
                od_ton = (road_od.tons.get_original() +
                          rail_od.tons.get_derived())
                distance = road_od.dist
                category = road_od.tons.category
                coeff = self._get_derivation_coefficient(od_ton, distance,
                                                         category)

                # derive road tons to railway
                rail_od_derivation = self.od_to_railway(road_od, coeff,
                                                        allow_original)

                # store reference to rail od pair derivation for reversion
                rail_od_derivations.append(rail_od_derivation)

        return rail_od_derivations

    def link_to_roadway(self, id_rail_link, gauge_rail_link,
                        allow_original=True):
        """Derive all possible rail od pairs that use rail_link to road."""

        # list to store road od pairs receiving derivated freight
        road_od_derivations = []

        # get rail link from the rail network
        rail_link = self.fn.rail.get_link(id_rail_link, gauge_rail_link)

        for rail_od in self.fn.rail.iter_od_pairs():

            use_rail_link = rail_link.id in rail_od.links
            use_same_gauge = rail_link.gauge == rail_od.gauge
            if use_rail_link and use_same_gauge:

                # derive rail tons to roadway
                COEFF = 1.0
                road_od_derivation = self.od_to_roadway(rail_od, COEFF,
                                                        allow_original)

                # store reference to road od pair derivation for reversion
                road_od_derivations.append(road_od_derivation)

        return road_od_derivations

    # PRIVATE
    def _derive_od(self, from_od, to_od, coeff, from_mode, to_mode,
                   allow_original=True):

        # get od pair caracteristics
        id_od = from_od.id
        category = from_od.tons.category

        # derive tons from from_od pair to to_od pair
        # from_mode.remove_mobility_requirements(from_od)
        # to_mode.remove_mobility_requirements(to_od)

        orig_ton_derived, returned_ton = from_od.derive_ton(to_od, coeff,
                                                            allow_original)

        # from_mode.increase_mobility_requirements(from_od)
        # to_mode.increase_mobility_requirements(to_od)

        # remove tons from "from_mode" links used by "from_od"
        for id_from_link in from_od.links:
            from_link = from_mode.get_link(id_from_link, from_od.gauge)
            from_link.tons.remove_original(ton=orig_ton_derived,
                                           categories=category,
                                           id_ods=id_od)
            from_link.tons.remove_derived(ton=returned_ton,
                                          categories=category,
                                          id_ods=id_od)
        # regroup links from "from_mode", if necessary
        # for id_from_link in from_od.links:
        #     from_link = from_mode.get_link(id_from_link, from_od.gauge)
        #     from_mode.regroup_link(from_link)

        # add derived tons to "to_mode" links, used by "to_od"
        for id_to_link in to_od.links:
            to_link = to_mode.get_link(id_to_link, to_od.gauge)
            to_link.tons.add_original(ton=returned_ton,
                                      categories=category,
                                      id_ods=id_od)
            to_link.tons.add_derived(ton=orig_ton_derived,
                                     categories=category,
                                     id_ods=id_od)

        # regroup links from "to_mode", if necessary
        # for id_to_link in to_od.links:
        #     to_link = to_mode.get_link(id_to_link, to_od.gauge)
        #     to_mode.regroup_link(to_link)

    def _road_od_pair_is_derivable(self, road_od):
        """Indicate if an od pair is derivable or not.

        Args:
            road_od: OD pair that will be checked to be derivable to railway.
        """

        # firts check origin != destination and product category derivable
        if road_od.is_intrazone() or road_od.tons.category == 0:
            return False

        # check if there is an operable railway path for the od pair
        has_railway_path = self.fn.rail.has_railway_path(road_od)
        if not has_railway_path:
            return False

        # calculate original road tons
        id_od = road_od.id
        category_od = road_od.tons.category
        if self.fn.rail.has_od(id_od, category_od):
            rail_od = self.fn.rail.get_od(id_od, category_od)
            orig_road_ton = (road_od.tons.get_original() +
                             rail_od.tons.get_derived())
        else:
            orig_road_ton = road_od.tons.get_original()

        # check if od pair meet minimum tons adn distance to be derivable
        min_ton = orig_road_ton > self.fn.rail.params[
            "min_tons_to_derive"].value
        min_dist = road_od.dist > self.fn.rail.params[
            "min_dist_to_derive"].value

        # check if railway path distance is not excesively longer than road
        max_diff = self.fn.rail.params["max_path_difference"].value
        dist_rail = self.fn.rail.get_path_distance(road_od)
        dist_road = self.fn.road.get_path_distance(road_od)
        railway_path_is_plausible = abs(dist_rail / dist_road - 1) < max_diff

        is_derivable = min_ton and min_dist and railway_path_is_plausible

        return is_derivable

    def _get_derivation_coefficient(self, od_ton, distance, category):
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
        max_dist = float(self.fn.rail.params["dist_of_max_derivation"].value)
        min_dist = float(self.fn.rail.params["min_dist_to_derive"].value)
        max_tons = float(self.fn.rail.params["tons_of_max_derivation"].value)
        min_tons = float(self.fn.rail.params["min_tons_to_derive"].value)

        # get maximum derivation depending on od product category
        param_name = "max_derivation_" + str(category)
        if param_name in self.fn.rail.params:
            max_deriv = float(self.fn.rail.params[param_name].value)
        else:
            max_deriv = float(self.fn.rail.params["max_derivation"].value)

        # assign max derivation if distance and tons are greater than max
        if distance >= max_dist and od_ton >= max_tons:
            deriv_coefficient = max_deriv

        # assign zero derivation if distance and tons are lower than min
        elif distance <= min_dist and od_ton >= min_tons:
            deriv_coefficient = 0.0

        # interpolate derivation coefficient otherwise
        else:

            # calculate substitution coefficient for tons / dist
            coef_ton_dist = (max_tons - min_tons) / (max_dist - min_dist)

            # get tons and distance relevant to interpolate
            # if one of the two dimensions exceeds maximum, maximum will be
            # used
            tons = min(od_ton, max_tons)
            dist = min(distance, max_dist)

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


class FreightNetwork():

    """Represents a freight network with rail and road modes of transport.

    FreightNetwork uses RailwayNetwork and RoadNetwork objects to represent a
    bimodal freight transport network. It uses those classes to cost all
    freight network and can derive traffic from one mode of transport to the
    other, exploring changes in overall cost of different traffic
    configurations."""

    LINKS_OPTIMIZATION_CLASS = WeakLinksAggregator
    ODS_OPTIMIZATION_CLASS = WeakOdsAggregator
    REROUTING_OPTIMIZATION_CLASS = LinksTrafficRerouter

    def __init__(self, railway_network=None, roadway_network=None,
                 projection_factor=1.0, restrictions=False):

        self.rail = railway_network or RailwayNetwork(
            projection_factor=projection_factor, restrictions=restrictions)

        self.road = roadway_network or RoadwayNetwork(
            projection_factor=projection_factor, restrictions=restrictions)

        self.derive = DerivationMethods(self)
        self.reroute = ReroutingMethods(self)

    # PUBLIC
    # iters and getters
    def iter_rail_links(self, sorted_by=None):

        # iterate rail links with no order
        if not sorted_by:
            for rail_link in self.rail.iter_links():
                yield rail_link

        # iterate rail links ordering them by an attribute
        else:
            for rail_link in sorted(self.rail.iter_links()):
                yield rail_link

    def iter_rail_ods(self, sorted_by=None):

        # iterate rail links with no order
        if not sorted_by:
            for rail_od in self.rail.iter_od_pairs():
                yield rail_od

        # iterate rail links ordering them by an attribute
        else:
            for rail_od in sorted(self.rail.iter_od_pairs()):
                yield rail_od

    @property
    def total_cost(self):
        return self.rail.total_cost + self.road.total_cost

    # costing methods
    def cost_network(self):
        """Cost total freight transport network."""
        self.rail.cost_network()
        self.road.cost_network()

    # optimizing strategies
    def min_network_cost_deriving_links(self):
        """Find modal split with minimum overall cost analyzing links.

        Derive traffic from one mode to the other looking for the minimum
        overall cost of freight transportation.

        The algorithm starts with maximum possible traffic derivation to
        railway and then move back all the traffic of one link at a time, from
        railway to roadway, looking to reduce overall cost of the entire
        bimodal network by disabling railway tracks (ie, the links).

        At first sight, there is no way to know what combination of freed
        railway links will reduce the overall cost from the scenario of maximum
        traffic derivation to railway."""

        self.cost_network()
        self.LINKS_OPTIMIZATION_CLASS(self).optimize()

    def min_network_cost_deriving_ods(self):
        """Find modal split with minimum overall cost analyzing od pairs.

        Derive traffic from one mode to the other looking for the minimum
        overall cost of freight transportation.

        The algorithm starts with maximum possible traffic derivation to
        railway and then move back all the traffic of one od pair at a time,
        from railway to roadway, looking to reduce overall cost of the entire
        bimodal network by moving back those od pairs less convinient to the
        railway mode.

        At first sight, there is no way to know what combination of freed
        railway links will reduce the overall cost from the scenario of maximum
        traffic derivation to railway."""

        self.cost_network()
        self.ODS_OPTIMIZATION_CLASS(self).optimize()

    def min_network_cost_rerouting_links(self):
        """Find modal split with minimum overall cost rerouting traffic.

        Remove railway links rerouting traffic through other links when
        possible and deriving to roadway when origin-destination pair turns to
        be impossible to be done in railway.

        The algorithm try to remove one railway link at a time rerouting
        traffic towards other links or moving it to roadway mode looking to
        reduce overall cost of the entire bimodal network by removing the less
        convinient links of the network.

        At first sight, there is no way to know what combination of freed
        railway links will reduce the overall cost."""

        self.cost_network()
        self.REROUTING_OPTIMIZATION_CLASS(self).optimize()

    def min_network_cost(self):
        self.derive.all_to_railway()
        self.min_network_cost_deriving_links()
        self.min_network_cost_deriving_ods()

    # report methods
    def report_to_excel(self, description=None, append_report=False):
        """Make a report of RailwayNetwork and RoadNetwork results.

        At any moment, freeze the status of RailwayNetwork and RoadNetwork
        into excel reports.

        Args:
            description: Description of the scenario result being reported.
            append_report: If False, new report replace previous one (excel
                file is being replaced). If True, new report is appended inside
                the old one.
        """
        if not append_report:
            BaseReport.create_new_global_report()

        self.rail.report_to_excel(description=description,
                                  append_report=append_report)
        self.road.report_to_excel(description=description,
                                  append_report=append_report)


def main():

    # initialize freight transport network
    fn = FreightNetwork(projection_factor=1.0, restrictions=False)

    # cost network at current situation
    scenario = "current situation"
    print "Costing", scenario
    fn.cost_network()
    fn.report_to_excel(scenario, append_report=False)

    # cost network deriving all possible freight to railway
    scenario = "derive all to railway"
    print "Costing", scenario
    fn.derive.all_to_railway()
    fn.cost_network()
    fn.report_to_excel(scenario, append_report=True)

    # cost network deriving all but some links and some od pairs
    scenario = "derive all to railway but some links and ods"
    print "Costing", scenario
    fn.min_network_cost()
    fn.cost_network()
    fn.report_to_excel(scenario, append_report=True)

    # cost network deriving all freight to roadway
    scenario = "derive all to roadway"
    print "Costing", scenario
    fn.derive.all_to_roadway()
    fn.cost_network()
    fn.report_to_excel(scenario, append_report=True)

    # WITH LINK RESTRICTIONS

    # initialize freight transport network
    fn = FreightNetwork(projection_factor=1.0, restrictions=True)

    # cost network at current situation
    scenario = "current situation RESTR"
    print "Costing", scenario
    fn.cost_network()
    fn.report_to_excel(scenario, append_report=True)

    # cost network deriving all possible freight to railway
    scenario = "derive all to railway RESTR"
    print "Costing", scenario
    fn.derive.all_to_railway()
    fn.cost_network()
    fn.report_to_excel(scenario, append_report=True)

    # cost network deriving all but some links and some od pairs
    scenario = "derive all to railway but some links and ods RESTR"
    print "Costing", scenario
    fn.min_network_cost()
    fn.cost_network()
    fn.report_to_excel(scenario, append_report=True)

    # cost network deriving all freight to roadway
    scenario = "derive all to roadway RESTR"
    print "Costing", scenario
    fn.derive.all_to_roadway()
    fn.cost_network()
    fn.report_to_excel(scenario, append_report=True)


if __name__ == '__main__':
    main()
