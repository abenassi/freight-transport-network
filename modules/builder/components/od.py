"""Path and OD classes are used either by Railway or Roadway networks."""


class BasePath():

    def get_links(self):
        return self.links

    def get_id(self):
        return self.id

    def _create_links_list(self):
        """Create list with all links used by OD path."""

        # create emtpy dict to store links
        links = []

        # check there is a path
        if self.path_nodes:

            # iterate through path nodes creating links
            for i in xrange(len(self.path_nodes) - 1):

                # take two consecutive nodes
                node_a = int(self.path_nodes[i])
                node_b = int(self.path_nodes[i + 1])

                # create link, putting first the node with less value
                if node_a < node_b:
                    link_id = "-".join([str(node_a), str(node_b)])

                else:
                    link_id = "-".join([str(node_b), str(node_a)])

                # add the link to the dict
                links.append(link_id)

        return links

    def _get_path_nodes(self):
        """Create list with all nodes in OD path."""

        # check if OD has no path (when O == D)
        if self.path and self.nodes[0] != self.nodes[1]:

            # if possible, split path in nodes
            try:
                return [int(i) for i in self.path.split("-")]

            # where path doesn't have "-" is not a valid path
            except:
                return None

        else:
            return None

    def _get_safe_id(self, id):
        """Return id properly built.

        ODs ids must be always created with number of lowest numeration node
        first and number of highest numeration node last.

            Right: 10-25
            Wrong: 25-10

        This method assures proper identification of od pairs."""

        nodes = [int(i) for i in id.split("-")]

        # check if first node is less than second one
        if nodes[0] < nodes[1]:
            id_checked = str(nodes[0]) + "-" + str(nodes[1])

        # change order of nodes in the id, if second node is less than first
        else:
            id_checked = str(nodes[1]) + "-" + str(nodes[0])

        return id_checked


class Path(BasePath):

    """Represents a railway or roadway path.

    Roadway paths are considered to have unique gauge."""

    def __init__(self, id, path, gauge):
        self.id = self._get_safe_id(id)
        self.path = path
        self.gauge = gauge
        self.nodes = [int(i) for i in self.id.split("-")]

        # path properties
        self.path_nodes = self._get_path_nodes()
        self.links = self._create_links_list()

    def __repr__(self):
        return "OD: " + self.id.ljust(10) + \
               "Path: " + self.path.ljust(70) + \
               "Gauge: " + str(self.gauge)


class OD(BasePath):

    """Represents an od pair in a railway or roadway network.

    It carries tons of freight and has path, gauge and distance. Roadway od
    pairs are considered to have unique gauge."""

    NF = "{:,.1f}"
    FIELDS = ["id_od", "gauge", "distance", "ton", "path"]

    def __init__(self, id, ton, path=None, gauge=None, dist=None):
        # identification properties
        self.id = self._get_safe_id(id)
        self.nodes = [int(i) for i in self.id.split("-")]

        # path properties
        self.path = path
        self.path_nodes = self._get_path_nodes()
        self.gauge = gauge
        self.dist = dist
        self.links = self._create_links_list()

        # traffic carried
        self.original_ton = ton
        self.derived_ton = 0.0

    def __repr__(self):
        return "OD: " + self.id.ljust(10) + \
               "Ton: " + self.NF.format(self.get_ton()).ljust(15) + \
               "Path: " + str(self.path).ljust(60) + \
               "Gauge:" + str(self.gauge).ljust(15) + \
               "Distance:" + str(self.dist)

    # PUBLIC
    # GET methods
    def get_original_ton(self):
        """Get tons that are originally transported by the transport mode."""
        return self.original_ton

    def get_derived_ton(self):
        """Get tons that are derived from other freight transport mode."""
        return self.derived_ton

    def get_ton(self):
        """Get total tons of od pair, original and derived freight."""
        return self.get_original_ton() + self.get_derived_ton()

    def get_attributes(self):
        return [self.id, self.gauge, self.dist, self.get_ton(), self.path]

    def get_dist(self):
        return self.dist

    # SET and ADD methods
    def add_original_ton(self, ton):
        """Add original tons to OD pair."""
        self.original_ton += ton

    def derive_ton(self, other, coeff=1.0):
        """Derive tons to another freight transport mode.

        It derives tons to an OD pair object coming from another transport mode
        but with the same id.

        Args:
            other: OD object from another transport mode that will receive
                derived tons from self OD object.
            coeff (opt): Coefficient of tons that will be derived. The default
                is to derive all tons (1.0)

        Raise:
            DerivationError: Trying to derive tons to an other od pair with
                different id will raise an error. Derivation must occur with an
                od pair with the same origin and destination (ie, same id)
        """

        # check od pairs have same id
        msg = "OD pairs are different: {} != {}".format(self.id, other.id)
        assert self.id == other.id, msg

        # calculate tons to derive
        tons_to_derive = self.get_ton() * coeff

        # remove tons from self od pair
        self.original_ton -= tons_to_derive

        # add tons to other od pair
        other.derived_ton += tons_to_derive

    def set_path(self, path, gauge):
        """Take a path and gauge and set it to the od pair."""

        # set data members
        self.path = path
        self.gauge = gauge

        # get path nodes from new path and create links dictionary
        self.path_nodes = self._get_path_nodes()
        self.links = self._create_links_list()

    # BOOL methods
    def has_declared_path(self):
        """Has a path data member, even if its a "not found" one."""
        return bool(self.path and self.gauge)

    def has_railway_path(self):
        """Has an operable railway path."""
        return bool(self.path and self.gauge) and "-" in self.path

    # OTHER methods
    def calc_distance(self, network_links):
        """Takes a dictionary with all network links and sum distance of od
        links to calculate distance of od pair."""

        # init distance with zero
        self.dist = 0

        # iterate through od used links adding its distance to od distance
        for od_link in self.links:

            try:
                # print network_links[od_link].dist
                self.dist += network_links[od_link][self.gauge].dist

            except:
                print od_link, self.gauge, "is missing in network links list!",
                print "od pair: ", self.id




