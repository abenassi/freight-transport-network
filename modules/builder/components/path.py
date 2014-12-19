class BasePath(object):

    # PUBLIC
    # others
    def calc_distance(self, network_links):
        """Takes a dictionary with all network links and sum distance of od
        links to calculate distance of od pair."""

        # init distance with zero
        dist = 0

        # iterate through od used links adding its distance to od distance
        for od_link in self.links:

            try:
                dist += network_links[od_link][self.gauge].dist

            except:
                print od_link, self.gauge, "is missing in network links list!",
                print "od pair: ", self.id

        return dist

    def is_intrazone(self):
        """Check if origin = destination."""
        return len(self.nodes) == 2 and self.nodes[0] == self.nodes[1]

    # PRIVATE
    def _create_links_list(self, path_nodes):
        """Create list with all links used by OD path."""

        # create emtpy dict to store links
        links = []

        # check there is a path
        if path_nodes:

            # iterate through path nodes creating links
            for i in xrange(len(path_nodes) - 1):

                # take two consecutive nodes
                node_a = int(path_nodes[i])
                node_b = int(path_nodes[i + 1])

                # create link, putting first the node with less value
                if node_a < node_b:
                    link_id = "-".join([str(node_a), str(node_b)])

                else:
                    link_id = "-".join([str(node_b), str(node_a)])

                # add the link to the dict
                links.append(link_id)

        return links

    def _get_path_nodes(self, path):
        """Create list with all nodes in OD path."""

        if self.is_intrazone():
            return None

        elif path:

            # if possible, split path in nodes
            try:
                nodes = [int(i) for i in path.split("-")]

                if nodes[-1] < nodes[0]:
                    nodes.reverse()

                return nodes

            # where path doesn't have "-" is not a valid path
            except:
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

    def _path_nodes_to_string(self, path_nodes):
        """Take a list of path nodes and return a string path with them."""

        if type(path_nodes) == list:
            path_nodes_str = [str(i) for i in path_nodes]
            return "-".join(path_nodes_str)

        elif type(path_nodes) == int:
            return path_nodes

        else:
            return None

class Path(BasePath):

    """Represents a railway or roadway path.

    Roadway paths are considered to have unique gauge."""

    def __init__(self, id, path, gauge):
        self.id = self._get_safe_id(id)
        self.nodes = [int(i) for i in self.id.split("-")]

        self.path_nodes = self._get_path_nodes(path)
        self.path = self._path_nodes_to_string(self.path_nodes)
        self.links = self._create_links_list(self.path_nodes)

        self.gauge = gauge

    def __repr__(self):
        return "OD: " + self.id.ljust(10) + \
               "Path: " + self.path.ljust(70) + \
               "Gauge: " + str(self.gauge)
