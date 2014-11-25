from tons import OdTons

"""Path and OD classes are used either by Railway or Roadway networks."""


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


class OdCostData():

    def __init__(self):
        self.deposit = None
        self.short_freight = None
        self.immo_value = None


class OdCostMethods():

    def __init__(self):
        self.cost = OdCostData()

    # getters
    def get_deposit_cost(self):
        return self.cost.deposit

    def get_short_freight_cost(self):
        return self.cost.short_freight

    def get_immo_value_cost(self):
        return self.cost.immo_value

    # setters
    def set_deposit_cost(self, deposit_cost):
        self.cost.deposit = deposit_cost

    def set_short_freight_cost(self, short_freight_cost):
        self.cost.short_freight = short_freight_cost

    def set_immo_value_cost(self, immo_value_cost):
        self.cost.immo_value = immo_value_cost


class OD(OdTons, BasePath, OdCostMethods):

    """Represents an od pair in a railway or roadway network.

    It carries tons of freight and has path, gauge and distance. Roadway od
    pairs are considered to have unique gauge."""

    NF = "{:,.1f}"
    FIELDS = ["id_od", "gauge", "distance", "original ton", "derived ton",
              "ton", "railway_category", "path", "id_lowest_link",
              "ton_lowest_link", "deposit_cost", "short_freight_cost",
              "immo_value_cost"]

    def __init__(self, id, ton, path=None, gauge=None, dist=None,
                 rail_category=None):

        # call constructors of superclasses
        super(OD, self).__init__()

        # identification properties
        self.id = self._get_safe_id(id)
        self.nodes = [int(i) for i in self.id.split("-")]

        # path properties
        self.path = path
        self.path_nodes = self._get_path_nodes()
        self.gauge = gauge
        self.dist = dist
        self.links = self._create_links_list()

        # traffic properties
        self.add_original_ton(ton)
        self.rail_category = rail_category
        self.lowest_link = None

        self.cost = OdCostData()

    def __repr__(self):
        return "OD: " + self.id.ljust(10) + \
               "Ton: " + self.NF.format(self.get_ton()).ljust(15) + \
               "Gauge:" + str(self.gauge).ljust(15) + \
               "Distance:" + str(self.dist).ljust(15) + \
               "Category:" + str(self.rail_category)

    def __lt__(self, other):
        return self.get_ton() < other.get_ton()

    # PUBLIC
    # getters
    def get_attributes(self):
        return [self.id, self.gauge, self.dist, self.get_original_ton(),
                self.get_derived_ton(), self.get_ton(), self.get_category(),
                self.path, self.get_lowest_link_id(),
                self.get_lowest_link_scale(), self.get_deposit_cost(),
                self.get_short_freight_cost(), self.get_immo_value_cost()]

    def get_dist(self):
        return self.dist

    def get_category(self):
        return self.rail_category

    def get_lowest_link_scale(self):
        """Returns the tons passing through the lowest link used by OD pair.

        It is a mesure used to calculate the frequency that train services can
        have for the OD pair, taking into account the worst part of the path,
        in terms of the scale reached."""

        if self.lowest_link:
            return self.lowest_link.get_ton()

        else:
            return None

    def get_lowest_link_id(self):
        """Returns the tons passing through the lowest link used by OD pair.

        It is a mesure used to calculate the frequency that train services can
        have for the OD pair, taking into account the worst part of the path,
        in terms of the scale reached."""

        if self.lowest_link:
            return self.lowest_link.get_id()

        else:
            return None

    # cost getters
    def calc_distance(self, network_links):
        self.dist = super(OD, self).calc_distance(network_links)

    # setters
    def set_path(self, path, gauge):
        """Take a path and gauge and set it to the od pair."""

        # set data members
        self.path = path
        self.gauge = gauge

        # get path nodes from new path and create links dictionary
        self.path_nodes = self._get_path_nodes()
        self.links = self._create_links_list()

    def set_category(self, category_od):
        self.rail_category = category_od

    def set_lowest_scale_link(self, link):
        self.lowest_link = link

    # BOOL methods
    def has_declared_path(self):
        """Has a path data member, even if its a "not found" one."""
        return bool(self.path and self.gauge)

    def is_intrazone(self):
        """Check if origin = destination."""
        return len(self.nodes) == 2 and self.nodes[0] == self.nodes[1]

    def has_operable_path(self):
        """Has a positive path that can be operated."""
        return self.has_declared_path() and self.path_nodes
