class Link():

    """Base class for a link in a freight transport network."""

    def __init__(self, id, distance, gauge):
        # identification properties
        self.id = id
        self.gauge = gauge
        self.nodes = [int(i) for i in id.split("-")]

        # static properties
        self.dist = float(distance)  # Km

        # traffic parameters
        self.original_ton = 0.0  # original ton of freight
        self.derived_ton = 0.0  # derived ton of freight
        self.gross_tk = None  # gross ton-km

        # track costs
        self.eac_track = None
        self.maintenance = None

    def __repr__(self):
        return "Link: " + str(self.get_id()).ljust(10) + \
               "Distance: {:,.1f}".format(self.get_dist()).ljust(18) + \
               "Gauge: " + str(self.get_gauge()).ljust(8) + \
               "Ton: {:,.1f}".format(self.get_ton()).ljust(20)

    # PUBLIC
    def add_original_ton(self, ton):
        self.original_ton += ton

    def remove_original_ton(self, ton):
        self.original_ton -= ton

    def add_derived_ton(self, ton):
        self.derived_ton += ton

    def remove_derived_ton(self, ton):
        self.derived_ton -= ton

    def get_original_ton(self):
        return self.original_ton

    def get_derived_ton(self):
        return self.derived_ton

    def get_ton(self):
        return self.get_original_ton() + self.get_derived_ton()

    def get_dist(self):
        return self.dist

    def get_id(self):
        return self.id


class RoadwayLink(Link):
    """Represents a link in a roadway network."""
    pass


class RailwayLink(Link):

    """Represents a link in a railway network.

    It keeps track of tons passing and idle capacity of tons that could be
    supported with the same rolling material currently running."""

    FIELDS = ["id_link", "gauge", "distance", "original_tons", "derived_tons",
              "tons", "idle_capacity_regroup", "idle_capacity_no_regroup",
              "detour_cost", "track_cost", "maintenance_cost", "gross ton-km"]

    # traffic parameters
    idle_capacity_regroup = 0.0  # ton-km
    idle_capacity_no_regroup = 0.0  # ton-km

    # track costs
    eac_detour = None

    def __repr__(self):
        return "Link: " + str(self.id).ljust(10) + \
               "Distance: {:,.1f}".format(self.dist).ljust(18) + \
               "Gauge: " + str(self.gauge).ljust(8) + \
               "Ton: {:,.1f}".format(self.get_ton()).ljust(20) + \
               "Idle capacity: {:,.1f}".format(self.get_idle_cap_in_tons())

    # PUBLIC
    def get_attributes(self):
        return [self.id, self.gauge, self.dist, self.original_ton,
                self.derived_ton, self.get_ton(), self.idle_capacity_regroup,
                self.idle_capacity_no_regroup, self.eac_detour,
                self.eac_track, self.maintenance, self.gross_tk]

    def add_idle_cap_regroup(self, idle_capacity_ton):
        """Add idle capacity passed in ton, that can be removed."""
        self.idle_capacity_regroup += idle_capacity_ton

    def add_idle_cap_no_regroup(self, idle_capacity_ton):
        """Add idle capacity passed in ton, that can not be removed."""
        self.idle_capacity_no_regroup += idle_capacity_ton

    def get_idle_cap_in_ton_km(self):
        """Returns idle capacity in ton-km."""
        return (self.idle_capacity_regroup +
                self.idle_capacity_no_regroup) * self.dist

    def get_idle_cap_in_tons(self):
        """Returns idle capacity in ton-km."""
        return self.idle_capacity_regroup + self.idle_capacity_no_regroup

    def get_idle_cap_regroup(self):
        """Returns idle capacity in ton-km, that can be removed."""
        return self.idle_capacity_regroup

    def get_idle_cap_no_regroup(self):
        """Returns idle capacity in ton-km, that can not be removed."""
        return self.idle_capacity_no_regroup

    def regroup(self, idle_capacity_ton):
        """Eliminate idle capacity passed in ton."""

        # check if link has that idle capacity
        if self.idle_capacity_regroup - idle_capacity_ton < 0:
            msg = "{} has no {} idle capacity!".format(self.id,
                                                       idle_capacity_ton)

            raise ValueError(msg)

        self.idle_capacity_regroup -= idle_capacity_ton

    def revert_regroup(self, idle_capacity_ton):
        """Regain idle capacity passed in ton."""
        self.idle_capacity_regroup += idle_capacity_ton

    def get_gross_ton_km(self, wagon_capacity, wagon_weight,
                         locomotive_capacity, locomotive_weight):
        """Take rolling material parameters and calculate gross ton_km."""

        # wagons weight
        num_wagons = self.get_ton() / wagon_capacity
        wagons_weight = num_wagons * wagon_weight

        # locomotives weight
        num_locoms = (self.get_ton() +
                      self.get_idle_cap_in_tons()) / locomotive_capacity
        locoms_weight = num_locoms * locomotive_weight

        return (wagons_weight + locoms_weight + self.get_ton()) * self.dist


def test():

    print "\nCreate a link"
    print "-----------"
    link = RailwayLink("1009-1003", 150.4, "ancha")

    print link

if __name__ == '__main__':
    test()
