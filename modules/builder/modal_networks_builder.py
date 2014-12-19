from xl_input import XlLoadParam, XlLoadOD, XlLoadRailwayLink, XlLoadPath
from xl_input import XlLoadRoadwayLink
from components import RollingMaterial, OD


class BaseModalNetworkBuilder(object):

    """Base builder of a modal network.

    It must be subclassed to build up a RailwayNetwork or a RoadwayNetwork."""

    def __init__(self, xl_parameters=None, xl_od_pairs=None, xl_links=None,
                 xl_paths=None, xl_od_pairs_current=None,
                 xl_restricted_links=None):
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
        self.xl_restricted_links = (xl_restricted_links or
                                    self.XL_RESTRICTED_LINKS)
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
        self._load_od_pairs_from_xl(mn.od_pairs, mn.projection_factor)
        print "Loading restricted links..."
        self._load_links_from_xl(self.xl_restricted_links, mn.restricted_links)
        print "Loading links..."
        self._load_links_from_xl(self.xl_links, mn.links)
        print "Loading paths..."
        self._load_from_xl(XlLoadPath, self.xl_paths, mn.paths)

        if mn.restrictions:
            self._remove_restricted_links(mn)

        self._find_paths(mn)

        self._calculate_od_distances(mn)

        self._calculate_link_tons(mn)

        mn.find_lowest_scale_links()

    def create_od_pair(self, mn, id_od, category_od):

        # create od pair object
        od = OD(id_od, 0.0)
        od.tons.category = category_od

        # assign path
        path_obj = mn.get_path(od.id)
        path = path_obj.path
        gauge = path_obj.gauge
        od.set_path(path, gauge)

        # calculate distance
        od.calc_distance(mn.links)

        # check od_pair id is in the network
        if id_od not in mn.od_pairs:
            mn.od_pairs[id_od] = {}

        # add new od pair
        mn.od_pairs[id_od][category_od] = od

    # PRIVATE
    def _remove_restricted_links(self, mn):

        for link in mn.iter_links(restricted=True):
            if (link.id in mn.links) and (link.gauge in mn.links[link.id]):
                mn.remove_link(link.id, link.gauge)

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

    def _load_od_pairs_from_xl(self, od_pairs, projection_factor):
        """Iterate an excel with data using a specific loader_class and storing
        results to output_dict."""

        for od in XlLoadOD(self.xl_od_pairs):

            od.project(projection_factor)

            # add id if its not in output_dict
            if od.id not in od_pairs:
                od_pairs[od.id] = {}

            # if category doesn't exist, add the od_pair
            if od.tons.category not in od_pairs[od.id]:
                od_pairs[od.id][od.tons.category] = od

            # if category already exist, udpate tons rather than replace elemen
            else:
                curr_od = od_pairs[od.id][od.tons.category]
                curr_od.tons.add_original(od.tons.get())

    def _find_paths(self, mn):
        """Iterate through od_pairs looking for path if not already passed."""

        # iterate all od_pairs
        for od in mn.iter_od_pairs():

            # check if od_pair doesn't have a path
            if (not od.has_declared_path()):

                # try to assign path and gauge asking path to the modal network
                try:
                    path_obj = mn.get_path(od.id)
                    path = path_obj.path
                    gauge = path_obj.gauge
                    od.set_path(path, gauge)

                # remove od pair if modal network has no path for it
                except:
                    print "Attention:", od.id, "has no path in " + \
                          mn.MODE_NAME + " network. Has been removed from this network."
                    mn.remove_od(od.id)

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
        MAX_EXCEPTIONS = 20
        for id_link in od.links:

            assert exception_counter < MAX_EXCEPTIONS, "Too many error paths."

            # try to update tons of a link_gauge
            try:
                link = mn.links[id_link][od.gauge]
                link.tons.add_original(ton=od.tons.get(),
                                       categories=od.tons.category,
                                       id_ods=od.id)

            # if impossible, there is no link-gauge in the network for od_pair
            except:
                exception_counter += 1
                print "".join(("There is no link ", id_link, " and gauge ",
                               od.gauge, " for od pair ", od.id,
                               " with path: ", od.path))


class RoadwayNetworkBuilder(BaseModalNetworkBuilder):

    XL_PARAMETERS = "data/roadway_parameters.xlsx"
    XL_OD_PAIRS = "data/roadway_od_pairs.xlsx"
    XL_RESTRICTED_LINKS = "data/roadway_restricted_links.xlsx"
    XL_LINKS = "data/roadway_links.xlsx"
    XL_PATHS = "data/roadway_paths.xlsx"

    def build(self, rn):
        """Builds a RoadwayNetwork object.

        Args:
            rn: a RoadwayNetwork object to be built.
        """

        super(RoadwayNetworkBuilder, self).build(rn)

        self._set_link_parameters(rn)

        print "RoadwayNetwork object has been succesfully built.\n"

    def _set_link_parameters(self, rn):
        """Set parameters to calculate number of detours needed per link."""

        for link in rn.iter_links():

            link.net_to_gross_factor = rn.params["net_to_gross_factor"].value

    def _load_links_from_xl(self, xl_links, links):
        """Iterate an excel with data using a specific loader_class and storing
        results to output_dict."""

        for link in XlLoadRoadwayLink(xl_links):

            # add link.id entry if not already in output dict
            if link.id not in links:
                links[link.id] = {}

            # add the link using id and gauge as keys
            links[link.id][link.gauge] = link


class RailwayNetworkBuilder(BaseModalNetworkBuilder):

    XL_PARAMETERS = "data/railway_parameters.xlsx"
    XL_OD_PAIRS = "data/railway_od_pairs.xlsx"
    XL_RESTRICTED_LINKS = "data/railway_restricted_links.xlsx"
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

        # set link parameters
        self._set_link_parameters(rn)

        print "RailwayNetwork object has been succesfully built.\n"

    def _load_links_from_xl(self, xl_links, links):
        """Iterate an excel with data using a specific loader_class and storing
        results to output_dict."""

        for link in XlLoadRailwayLink(xl_links):

            # add link.id entry if not already in output dict
            if link.id not in links:
                links[link.id] = {}

            # add the link using id and gauge as keys
            links[link.id][link.gauge] = link

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

    def _set_link_parameters(self, rn):
        """Set parameters to calculate number of detours needed per link."""

        for link in rn.iter_links():
            turnout_max_density = rn.params["turnout_freq_max_density"].value

            link.turnout_max_density = turnout_max_density
            link.turnout_freq = rn.params["turnout_freq"].value
            link.net_to_gross_factor = rn.params["net_to_gross_factor"].value
