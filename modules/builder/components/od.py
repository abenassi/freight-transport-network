from tons import OdTons
from path import BasePath

"""OD classes are used either by Railway or Roadway networks."""


class OdCost():

    def __init__(self):
        self.deposit = None
        self.short_freight = None
        self.immo_value = None


class OD(BasePath):

    """Represents an od pair in a railway or roadway network.

    It carries tons of freight and has path, gauge and distance. Roadway od
    pairs are considered to have unique gauge."""

    NF = "{:,.1f}"
    FIELDS = ["id_od", "gauge", "distance", "original ton", "derived ton",
              "ton", "railway_category", "path", "id_lowest_link",
              "ton_lowest_link", "deposit_cost", "short_freight_cost",
              "immo_value_cost"]

    def __init__(self, id, ton, path=None, gauge=None, dist=None,
                 category=None):

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
        self.lowest_link = None

        self.tons = OdTons(ton, category)
        self.cost = OdCost()

    def __repr__(self):
        return "OD: " + self.id.ljust(10) + \
               "Ton: " + self.NF.format(self.tons.get()).ljust(15) + \
               "Gauge:" + str(self.gauge).ljust(15) + \
               "Distance:" + str(self.dist).ljust(15) + \
               "Category:" + str(self.tons.category)

    def __lt__(self, other):
        return self.tons.get() < other.tons.get()

    # PUBLIC
    # getters
    def get_attributes(self):
        return [self.id, self.gauge, self.dist, self.tons.get_original(),
                self.tons.get_derived(), self.tons.get(), self.tons.category,
                self.path, self.get_lowest_link_id(),
                self.get_lowest_link_scale(), self.cost.deposit,
                self.cost.short_freight, self.cost.immo_value]

    def get_lowest_link_scale(self):
        """Returns the tons passing through the lowest link used by OD pair.

        It is a mesure used to calculate the frequency that train services can
        have for the OD pair, taking into account the worst part of the path,
        in terms of the scale reached."""

        if self.lowest_link:
            return self.lowest_link.tons.get()

        else:
            return None

    def get_lowest_link_id(self):
        """Returns the tons passing through the lowest link used by OD pair.

        It is a mesure used to calculate the frequency that train services can
        have for the OD pair, taking into account the worst part of the path,
        in terms of the scale reached."""

        if self.lowest_link:
            return self.lowest_link.id

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

    def project(self, projection_factor=1.0):
        self.tons.project(projection_factor)

    def revert_project(self):
        self.tons.revert_project()

    def derive_ton(self, other, coeff=1.0, allow_original=True):
        """Derive tons to another freight transport mode.

        It derives tons to an OD pair object coming from another transport mode
        but with the same id. Only original tons of the od pair are subject to
        derivation coefficient (coeff), while previously derivated tons are
        just returned completely

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

        # check od pairs have same id and category
        msg = "OD pairs are different: {} != {}".format(self.id,
                                                        other.id)
        assert self.id == other.id, msg

        msg = "OD pairs are different: {} != {}".format(self.tons.category,
                                                        other.tons.category)
        assert self.tons.category == other.tons.category, msg

        ton_to_derive, ton_to_return = self.tons.derive(other.tons, coeff,
                                                        allow_original)

        return (ton_to_derive, ton_to_return)
