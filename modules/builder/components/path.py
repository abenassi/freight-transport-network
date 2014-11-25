class BasePath(object):

    # PUBLIC
    def get_links(self):
        return self.links

    def get_id(self):
        return self.id

    def get_path(self):
        return self.path

    def get_gauge(self):
        return self.gauge

    def calc_distance(self, network_links):
        """Takes a dictionary with all network links and sum distance of od
        links to calculate distance of od pair."""

        # init distance with zero
        dist = 0

        # iterate through od used links adding its distance to od distance
        for od_link in self.links:

            try:
                dist += network_links[od_link][self.gauge].get_dist()

            except:
                print od_link, self.gauge, "is missing in network links list!",
                print "od pair: ", self.id

        return dist

    # PRIVATE
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
