from railway_xl_input import XlLoadParam, XlLoadOD, XlLoadLink, XlLoadPath
from components import RollingMaterial


class RailwayNetworkBuilder():

    XL_PARAMETERS = "data/railway_parameters.xlsx"
    XL_OD_PAIRS = "data/railway_od_pairs.xlsx"
    XL_OD_PAIRS_CURRENT = "data/railway_od_pairs_current.xlsx"
    XL_LINKS = "data/railway_links.xlsx"
    XL_PATHS = "data/railway_paths.xlsx"

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
        self.xl_od_pairs_current = xl_od_pairs_current or self.XL_OD_PAIRS_CURRENT
        self.xl_links = xl_links or self.XL_LINKS
        self.xl_paths = xl_paths or self.XL_PATHS

    # PUBLIC
    def build_railway_network(self, rn):
        """Builds a RailwayNetwork object.

        Take data from excel files to build a rail network model.

        Args:
            rn: a RailwayNetwork object to be built.
        """

        # load parameters, od_pairs and links to the RailwayNetwork object
        print "Loading parameters..."
        self._load_from_xl(XlLoadParam, self.xl_parameters, rn.params)
        print "Loading derived od pairs..."
        self._load_od_pairs_from_xl(XlLoadOD, self.xl_od_pairs, rn.od_pairs)
        print "Loading current od pairs..."
        self._load_od_pairs_from_xl(XlLoadOD, self.xl_od_pairs_current,
                                    rn.od_pairs_current)
        print "Loading links..."
        self._load_links_from_xl(XlLoadLink, self.xl_links, rn.links)
        print "Loading paths..."
        self._load_from_xl(XlLoadPath, self.xl_paths, rn.paths)

        # find path for each od pair
        self._find_paths(rn)

        # calculate distance of od pairs from link distances data
        self._calculate_od_distances(rn)

        # set rolling material parameters
        self._set_rolling_material_parameters(rn)

        print "RailwayNetwork object has been succesfully built.\n"

    # PRIVATE
    def _load_from_xl(self, loader_class, xl_name, output_dict):
        """Iterate an excel with data using a specific loader_class and storing
        results to output_dict."""

        for element in loader_class(xl_name):

            # check if element id was already in output_dict
            if not element.id in output_dict:
                output_dict[element.id] = element

            else:
                print "Warning", element.id, "is repeated in", xl_name

    def _load_od_pairs_from_xl(self, loader_class, xl_name, output_dict):
        """Iterate an excel with data using a specific loader_class and storing
        results to output_dict."""

        for element in loader_class(xl_name):

            # check that element id was not already in output_dict
            if not element.id in output_dict:
                output_dict[element.id] = element

            # if it is, update the element tons rather than replace it
            else:
                output_dict[element.id].ton += element.ton

    def _load_links_from_xl(self, loader_class, xl_name, output_dict):
        """Iterate an excel with data using a specific loader_class and storing
        results to output_dict."""

        for element in loader_class(xl_name):

            # add element.id entry if not already in output dict
            if not element.id in output_dict:
                output_dict[element.id] = {}

            # add the element using id and gauge as keys
            output_dict[element.id][element.gauge] = element

    def _set_rolling_material_parameters(self, rn):
        """Set operating parameters for rolling material objects, using
        parameters dictionary loaded to RailwayNetwork object."""

        # create empty RollingMaterial objects for wagons and locomotives
        rn.wagons = RollingMaterial()
        rn.locoms = RollingMaterial()

        # wagons
        rn.wagons.speed = rn.params["speed"].value
        rn.wagons.availability = rn.params["wagon_availability"].value
        rn.wagons.capacity = rn.params["wagon_capacity"].value
        rn.wagons.head_stops_time = rn.params[
            "wagon_head_stops_time"].value
        rn.wagons.turnout_time = rn.params["turnout_time"].value
        rn.wagons.turnout_freq = rn.params["turnout_freq"].value
        rn.wagons.regroup_time = rn.params["regroup_time"].value

        # locomotives
        rn.locoms.speed = rn.params["speed"].value
        rn.locoms.availability = rn.params["locomotive_availability"].value
        rn.locoms.capacity = rn.params["locomotive_capacity"].value
        rn.locoms.head_stops_time = rn.params[
            "locom_head_stops_time"].value
        rn.locoms.turnout_time = rn.params["turnout_time"].value
        rn.locoms.turnout_freq = rn.params["turnout_freq"].value
        rn.locoms.regroup_time = rn.params["regroup_time"].value

    def _find_paths(self, rn):
        """Iterate through od_pairs looking for path if not already passed."""

        # iterate all od_pairs
        for od_pair in rn.od_pairs.values() + rn.od_pairs_current.values():

            # check if od_pair doesn't have a path and RailwayNetwork has one
            if (not od_pair.has_declared_path()) and (od_pair.id in rn.paths):

                # assign path and gauge from RailwayNetwork.paths
                path = rn.paths[od_pair.id].path
                gauge = rn.paths[od_pair.id].gauge
                od_pair.set_path(path, gauge)

    def _calculate_od_distances(self, rn):
        """Uses links distances to calculate all od pair distances, storing
        results in each od object."""

        # iterate through all od pairs
        for od in rn.od_pairs.values() + rn.od_pairs_current.values():
            od.calc_distance(rn.links)
