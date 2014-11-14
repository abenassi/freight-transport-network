from modal_networks import RailwayNetwork, RoadwayNetwork
import sys
import numpy as np

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
    def derive_all_to_railway(self):
        """Derive all possible road od pairs from road mode to rail mode."""

        # iterate road od_pairs
        for road_od in self.road.iter_od_pairs():

            # check if od_pair is derivable
            if self._road_od_pair_is_derivable(road_od):

                # calculate proportion of tons to be derived
                rail_od = self.rail.get_od(road_od.get_id(),
                                           road_od.get_category())
                od_ton = road_od.get_original_ton() + rail_od.get_derived_ton()
                distance = road_od.get_dist()
                category = road_od.get_category()
                coeff = self._get_derivation_coefficient(od_ton, distance,
                                                         category)

                # derive road tons to railway
                self.derive_to_railway(road_od, coeff)

    def derive_all_to_roadway(self):
        """Derive all possible rail od pairs from rail mode to road mode."""

        # iterate road od_pairs
        for rail_od in self.rail.iter_od_pairs():

            # derive road tons to railway
            COEFF = 1.0
            self.derive_to_roadway(rail_od, COEFF)

    def cost_network(self):
        """Cost total freight transport network."""
        self.rail.cost_network()
        self.road.cost_network()

    def derive_to_railway(self, road_od, coeff):
        """Derive a road od pair to railway mode.

        Args:
            road_od: Road OD pair to be derived.
            coeff: Percentage of tons to be derived.
        """

        # first, calculate tons to be derived
        derived_tons = (road_od.get_original_ton() * coeff +
                        road_od.get_derived_ton())

        # derive tons from road_od pair to rail_od pair
        rail_od = self.rail.get_od(road_od.get_id(), road_od.get_category())
        road_od.derive_ton(rail_od, coeff)

        # remove tons from road links used by road od_pair
        for id_road_link in road_od.get_links():
            road_link = self.road.get_link(id_road_link, road_od.get_gauge())
            road_link.remove_ton(derived_tons)

        # add derived tons to rail links, used by rail od_pair
        for id_rail_link in rail_od.get_links():
            rail_link = self.rail.get_link(id_rail_link, rail_od.get_gauge())
            rail_link.add_derived_ton(derived_tons)

    def derive_to_roadway(self, rail_od, coeff):
        """Derive a rail od pair to roadway mode.

        Args:
            rail_od: Rail OD pair to be derived.
            coeff: Percentage of tons to be derived.
        """

        # first, calculate tons to be derived
        derived_tons = (rail_od.get_original_ton() * coeff +
                        rail_od.get_derived_ton())

        # derive tons from rail_od pair to road_od pair
        road_od = self.road.get_od(rail_od.get_id(), rail_od.get_category())
        rail_od.derive_ton(road_od, coeff)

        # remove tons from road links used by road od_pair
        for id_rail_link in rail_od.get_links():
            rail_link = self.rail.get_link(id_rail_link, rail_od.get_gauge())
            rail_link.remove_ton(derived_tons)

        # add derived tons to rail links, used by rail od_pair
        for id_road_link in road_od.get_links():
            road_link = self.road.get_link(id_road_link, road_od.get_gauge())
            road_link.add_derived_ton(derived_tons)

    def derive_link_to_railway(self, road_link):
        """Derive all possible road od pairs that use road_link to rail."""

        for road_od in self.road.iter_od_pairs():

            use_road_link = road_link.get_id() in road_od.get_links()
            use_same_gauge = road_link.get_gauge() == road_od.get_gauge()
            is_derivable = self._road_od_pair_is_derivable(road_od)
            if use_road_link and use_same_gauge and is_derivable:

                # calculate proportion of tons to be derived
                rail_od = self.rail.get_od(road_od.get_id(),
                                           road_od.get_category())
                od_ton = road_od.get_original_ton() + rail_od.get_derived_ton()
                distance = road_od.get_dist()
                category = road_od.get_category()
                coeff = self._get_derivation_coefficient(od_ton, distance,
                                                         category)

                # derive road tons to railway
                self.derive_to_railway(road_od, coeff)

    def derive_link_to_roadway(self, rail_link):
        """Derive all possible rail od pairs that use rail_link to road."""

        for rail_od in self.rail.iter_od_pairs():

            use_rail_link = rail_link.get_id() in rail_od.get_links()
            use_same_gauge = rail_link.get_gauge() == rail_od.get_gauge()
            if use_rail_link and use_same_gauge:

                # derive road tons to railway
                COEFF = 1.0
                self.derive_to_roadway(rail_od, COEFF)

    def min_network_cost_deriving_links(self):
        """Find the modal split with minimum overall cost.

        Derive traffic from one mode to the other looking for the minimum
        overall cost of freight transportation.

        The algorithm starts with maximum possible traffic derivation to
        railway and then move back all the traffic of one link at a time, from
        railway to roadway, looking to reduce overall cost of the entire
        bimodal network by disabling railway tracks (ie, the links).

        At first sight, there is no way to know what combination of freed
        railway links will reduce the overall cost from the scenario of maximum
        traffic derivation to railway."""
        pass

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
        self.rail.report_to_excel(description=description,
                                  append_report=append_report)
        self.road.report_to_excel(description=description,
                                  append_report=append_report)

    # PRIVATE
    def _road_od_pair_is_derivable(self, road_od):
        """Indicate if an od pair is derivable or not.

        Args:
            road_od: OD pair that will be checked to be derivable to railway.
        """

        # firts check origin != destination and product category derivable
        if road_od.is_intrazone() or road_od.get_category() == 0:
            return False

        # check if there is an operable railway path for the od pair
        has_railway_path = self.rail.has_railway_path(road_od)
        if not has_railway_path:
            return False

        # calculate original road tons
        id_od = road_od.get_id()
        category_od = road_od.get_category()
        if self.rail.has_od(id_od, category_od):
            rail_od = self.rail.get_od(id_od, category_od)
            orig_road_ton = (road_od.get_original_ton() +
                             rail_od.get_derived_ton())
        else:
            orig_road_ton = road_od.get_original_ton()

        # check if od pair meet minimum tons adn distance to be derivable
        min_ton = orig_road_ton > self.rail.params["min_tons_to_derive"].value
        min_dist = road_od.get_dist() > self.rail.params["min_dist_to_derive"].value

        # check if railway path distance is not excesively longer than road
        max_diff = self.rail.params["max_path_difference"].value
        dist_rail = self.rail.get_path_distance(road_od)
        dist_road = self.road.get_path_distance(road_od)
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
        max_dist = float(self.rail.params["dist_of_max_derivation"].value)
        min_dist = float(self.rail.params["min_dist_to_derive"].value)
        max_tons = float(self.rail.params["tons_of_max_derivation"].value)
        min_tons = float(self.rail.params["min_tons_to_derive"].value)

        # get maximum derivation depending on od product category
        param_name = "max_derivation_" + str(category)
        if param_name in self.rail.params:
            max_deriv = float(self.rail.params[param_name].value)
        else:
            max_deriv = float(self.rail.params["max_derivation"].value)

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


def main():
    """Some methods used here still does not work. Further design and
    implementation points to support this main method wich represent the user
    case."""

    # initialize freight transport networks
    rail = RailwayNetwork()
    road = RoadwayNetwork()
    fn = FreightNetwork(rail, road)

    # cost network at current situation
    scenario = "current situation"
    print "Costing", scenario
    fn.cost_network()
    fn.report_to_excel(scenario, append_report=False)

    # cost network deriving all possible freight to railway
    scenario = "derive all to railway"
    print "Costing", scenario
    fn.derive_all_to_railway()
    fn.cost_network()
    fn.report_to_excel(scenario, append_report=True)

    # cost network deriving all freight to roadway
    scenario = "derive all to roadway"
    print "Costing", scenario
    fn.derive_all_to_roadway()
    fn.cost_network()
    fn.report_to_excel(scenario, append_report=True)

if __name__ == '__main__':
    main()
