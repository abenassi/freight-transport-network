class BasePath():

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


class Path(BasePath):

    def __init__(self, id, path, gauge):
        self.id = id
        self.path = path
        self.gauge = gauge
        self.nodes = [int(i) for i in id.split("-")]

        # path properties
        self.path_nodes = self._get_path_nodes()
        self.links = self._create_links_list()

    def __repr__(self):
        return "OD: " + self.id.ljust(10) + \
               "Path: " + self.path.ljust(70) + \
               "Gauge: " + str(self.gauge)


class OD(BasePath):

    """Represents an od pair in a railway network.

    It carries tons of freight and has path, gauge and distance."""

    NF = "{:,.1f}"
    FIELDS = ["id_od", "gauge", "distance", "ton", "path"]

    def __init__(self, id, ton, path=None, gauge=None, dist=None):
        # identification properties
        self.id = id
        self.nodes = [int(i) for i in id.split("-")]

        # path properties
        self.path = path
        self.path_nodes = self._get_path_nodes()
        self.gauge = gauge
        self.dist = dist
        self.links = self._create_links_list()

        # traffic carried
        self.ton = ton

    def __repr__(self):
        return "OD: " + self.id.ljust(10) + \
               "Ton: " + self.NF.format(self.ton).ljust(15) + \
               "Path: " + str(self.path).ljust(60) + \
               "Gauge:" + str(self.gauge).ljust(15) + \
               "Distance:" + str(self.dist)

    # PUBLIC
    def get_attributes(self):
        return [self.id, self.gauge, self.dist, self.ton, self.path]

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
                print od_link, "is missing in network links list!"

    def has_declared_path(self):
        """Has a path data member, even if its a "not found" one."""
        return bool(self.path and self.gauge)

    def has_railway_path(self):
        """Has an operable railway path."""
        return bool(self.path and self.gauge) and "-" in self.path

    def set_path(self, path, gauge):
        """Take a path and gauge and set it to the od pair."""

        # set data members
        self.path = path
        self.gauge = gauge

        # get path nodes from new path and create links dictionary
        self.path_nodes = self._get_path_nodes()
        self.links = self._create_links_list()
