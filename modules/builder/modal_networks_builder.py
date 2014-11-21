from xl_input import XlLoadParam, XlLoadOD, XlLoadLink, XlLoadPath
from components import RollingMaterial, OD


class BaseModalNetworkBuilder(object):
    """Base builder of a modal network.

    It must be subclassed to build up a RailwayNetwork or a RoadwayNetwork."""

    def __init__(self, xl_parameters=None, xl_od_pairs=None, xl_links=None,
                 xl_paths=None, xl_od_pairs_current=None):
        """
        Args:
            xl_parameters: The path to excel file containing a list of general
                parameters of the rail network model.
            xl_od_pairs: The path to excel file containing a list of od_pairs
                and tons of freight carried in them.
            xl_links: The path to excel file containing a list of links between
                the nodes in the network, itd distance (km) and gauge.
            xl_paths: The path to excel file containing a list of paths
                assigned to od_pairs and its gauge.
            xl_od_pairs_current: The path to excel file containing a list of
                od_pairs and tons of freight carried in them currently by
                railway.
        """

        # loading parameters or defaults
        self.xl_parameters = xl_parameters or self.XL_PARAMETERS
        self.xl_od_pairs = xl_od_pairs or self.XL_OD_PAIRS
        self.xl_links = xl_links or self.XL_LINKS
        self.xl_paths = xl_paths or self.XL_PATHS

    # PUBLIC
    def build(self, mn):
        """Builds a modal network object.

        Take data from excel files to build up a model of a modal network.

        Args:
            mn: a modal network object to be built.
        """

        # load parameters, od_pairs and links to the RailwayNetwork object
        print "Loading parameters..."
        self._load_from_xl(XlLoadParam, self.xl_parameters, mn.params)
        print "Loading od pairs..."
        self._load_od_pairs_from_xl(mn.od_pairs)
        print "Loading links..."
        self._load_links_from_xl(mn.links)
        print "Loading paths..."
        self._load_from_xl(XlLoadPath, self.xl_paths, mn.paths)

        # find path for each od pair
        self._find_paths(mn)

        # calculate distance of od pairs from link distances data
        self._calculate_od_distances(mn)

        # set links parameters
        self._set_links_parameters(mn)

        # calculate tons carried by each link
        self._calculate_link_tons(mn)

        # store lowest link scale for each od pair
        mn.find_lowest_scale_links()

    def create_od_pair(self, mn, id_od, category_od):

        # create od pair object
        od_pair = OD(id_od, 0.0)
        od_pair.set_category(category_od)

        # assign path
        path = mn.paths[od_pair.get_id()].get_path()
        gauge = mn.paths[od_pair.get_id()].get_gauge()
        od_pair.set_path(path, gauge)

        # calculate distance
        od_pair.calc_distance(mn.links)

        # check od_pair id is in the network
        if id_od not in mn.od_pairs:
            mn.od_pairs[id_od] = {}

        # add new od pair
        mn.od_pairs[id_od][category_od] = od_pair

    # PRIVATE
    def _load_from_xl(self, loader_class, xl_name, output_dict):
        """Iterate an excel with data using a specific loader_class and storing
        results to output_dict."""

        # count repeated elements to stop loading if they exceed maximum
        repeated_counter = 0
        max_repeated = 200
        msg = "Too many ({}) repeated elements in {}".format(max_repeated,
                                                             xl_name)

        for element in loader_class(xl_name):

            assert repeated_counter < max_repeated, msg

            # check if element id was already in output_dict
            if element.id not in output_dict:
                output_dict[element.id] = element

            else:
                repeated_counter += 1
                print "Warning", element.id, "is repeated in", xl_name

    def _load_od_pairs_from_xl(self, od_pairs):
        """Iterate an excel with data using a specific loader_class and storing
        results to output_dict."""

        for od_pair in XlLoadOD(self.xl_od_pairs):

            # add id if its not in output_dict
            if od_pair.get_id() not in od_pairs:
                od_pairs[od_pair.get_id()] = {}

            # if category doesn't exist, add the od_pair
            if od_pair.get_category() not in od_pairs[od_pair.get_id()]:
                od_pairs[od_pair.get_id()][od_pair.get_category()] = od_pair

            # if category already exist, udpate tons rather than replace elemen
            else:
                curr_od = od_pairs[od_pair.get_id()][od_pair.get_category()]
                curr_od.add_original_ton(od_pair.get_ton())

    def _load_links_from_xl(self, links):
        """Iterate an excel with data using a specific loader_class and storing
        results to output_dict."""

        for link in XlLoadLink(self.xl_links):

            # add link.id entry if not already in output dict
            if link.id not in links:
                links[link.get_id()] = {}

            # add the link using id and gauge as keys
            links[link.id][link.gauge] = link

    def _find_paths(self, mn):
        """Iterate through od_pairs looking for path if not already passed."""

        # iterate all od_pairs
        for od_pair in mn.iter_od_pairs():

            # check if od_pair doesn't have a path and RailwayNetwork has one
            if (not od_pair.has_declared_path()) and (od_pair.get_id() in mn.paths):

                # assign path and gauge from RailwayNetwork.paths
                path = mn.paths[od_pair.id].path
                gauge = mn.paths[od_pair.id].gauge
                od_pair.set_path(path, gauge)

    def _calculate_od_distances(self, mn):
        """Uses links distances to calculate all od pair distances, storing
        results in each od object."""

        # iterate through all od pairs
        for od in mn.iter_od_pairs():
            od.calc_distance(mn.links)

    def _calculate_link_tons(self, mn):
        """Load tons of all od pairs to its used links."""

        # iterate through all od pairs
        for od in mn.iter_od_pairs():
            self._load_od_ton_to_links(mn, od)

    def _load_od_ton_to_links(self, mn, od):
        """Load tons of od pair to its used links."""

        # iterate links of od pair
        exception_counter = 0
        MAX_EXCEPTIONS = 50
        for id_link in od.get_links():

            assert exception_counter < MAX_EXCEPTIONS, "Too many error paths."

            # try to update tons of a link_gauge
            try:
                link = mn.get_links()[id_link][od.get_gauge()]
                link.add_original_ton(ton=od.get_ton(),
                                      categories=od.get_category(),
                                      id_ods=od.get_id())

            # if impossible, there is no link-gauge in the network for od_pair
            except:
                exception_counter += 1
                print "".join(("There is no link ", id_link, " and gauge ",
                               od.get_gauge(), " for od pair ", od.get_id(),
                               " with path: ", od.get_path()))

    def _set_links_parameters(self, mn):

        for link in mn.iter_links():
            link.net_to_gross_factor = mn.params["net_to_gross_factor"].value


class RoadwayNetworkBuilder(BaseModalNetworkBuilder):

    XL_PARAMETERS = "data/roadway_parameters.xlsx"
    XL_OD_PAIRS = "data/roadway_od_pairs.xlsx"
    XL_LINKS = "data/roadway_links.xlsx"
    XL_PATHS = "data/roadway_paths.xlsx"

    def build(self, rn):
        """Builds a RoadwayNetwork object.

        Args:
            rn: a RoadwayNetwork object to be built.
        """

        super(RoadwayNetworkBuilder, self).build(rn)

        print "RoadwayNetwork object has been succesfully built.\n"


class RailwayNetworkBuilder(BaseModalNetworkBuilder):

    XL_PARAMETERS = "data/railway_parameters.xlsx"
    XL_OD_PAIRS = "data/railway_od_pairs.xlsx"
    XL_LINKS = "data/railway_links.xlsx"
    XL_PATHS = "data/railway_paths.xlsx"

    # PUBLIC
    def build(self, rn):
        """Builds a RailwayNetwork object.

        Args:
            rn: a RailwayNetwork object to be built.
        """

        super(RailwayNetworkBuilder, self).build(rn)

        # set rolling material parameters
        self._set_rolling_material_parameters(rn)

        # set link detour parameters
        self._set_link_detour_parameters(rn)

        print "RailwayNetwork object has been succesfully built.\n"

    # PRIVATE
    def _set_rolling_material_parameters(self, rn):
        """Set operating parameters for rolling material objects, using
        parameters dictionary loaded to RailwayNetwork object."""

        # create empty RollingMaterial objects for wagons and locomotives
        rn.wagons = RollingMaterial()
        rn.locoms = RollingMaterial()

        # wagons
        rn.wagons.minimum_units = rn.params["wagon_min_units"].value
        rn.wagons.speed = rn.params["speed"].value
        rn.wagons.availability = rn.params["wagon_availability"].value
        rn.wagons.capacity = rn.params["wagon_capacity"].value
        rn.wagons.head_stops_time = rn.params["wagon_head_stops_time"].value
        rn.wagons.turnout_time = rn.params["turnout_time"].value
        rn.wagons.turnout_freq = rn.params["turnout_freq"].value
        rn.wagons.regroup_time = rn.params["regroup_time"].value

        # locomotives
        rn.locoms.minimum_units = rn.params["locomotive_min_units"].value
        rn.locoms.speed = rn.params["speed"].value
        rn.locoms.availability = rn.params["locomotive_availability"].value
        rn.locoms.capacity = rn.params["locomotive_capacity"].value
        rn.locoms.head_stops_time = rn.params["locom_head_stops_time"].value
        rn.locoms.turnout_time = rn.params["turnout_time"].value
        rn.locoms.turnout_freq = rn.params["turnout_freq"].value
        rn.locoms.regroup_time = rn.params["regroup_time"].value

    def _set_link_detour_parameters(self, rn):
        """Set parameters to calculate number of detours needed per link."""

        for link in rn.iter_links():

            link.set_turnout_freq(rn.params["turnout_freq"].value)

            turnout_max_density = rn.params["turnout_freq_max_density"].value
            link.set_turnout_max_density(turnout_max_density)
