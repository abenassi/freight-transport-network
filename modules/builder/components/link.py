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
    def reset(self):
        self.eac_track = None
        self.maintenance = None

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

    def get_ton_km(self):
        return self.get_ton() * self.get_dist()

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
              "detour_cost", "track_cost", "maintenance_cost", "gross ton-km",
              "num_detours"]

    # traffic parameters
    idle_capacity_regroup = 0.0  # ton-km
    idle_capacity_no_regroup = 0.0  # ton-km

    # detour parameters
    turnout_freq = None
    turnout_freq_max_density = None

    # track costs
    eac_detour = None

    def __repr__(self):
        return "Link: " + str(self.id).ljust(10) + \
               "Distance: {:,.1f}".format(self.dist).ljust(18) + \
               "Gauge: " + str(self.gauge).ljust(8) + \
               "Ton: {:,.1f}".format(self.get_ton()).ljust(20) + \
               "Idle capacity: {:,.1f}".format(self.get_idle_cap())

    # PUBLIC
    def set_turnout_freq(self, turnout_freq):
        self.turnout_freq = turnout_freq

    def set_turnout_max_density(self, turnout_freq_max_density):
        self.turnout_freq_max_density = turnout_freq_max_density

    def get_attributes(self):
        return [self.id, self.gauge, self.dist, self.original_ton,
                self.derived_ton, self.get_ton(), self.idle_capacity_regroup,
                self.idle_capacity_no_regroup, self.eac_detour,
                self.eac_track, self.maintenance, self.gross_tk,
                self.get_number_of_detours()]

    def add_idle_cap_regroup(self, idle_capacity_ton):
        """Add idle capacity passed in ton-km, that can be removed."""
        self.idle_capacity_regroup += idle_capacity_ton

    def add_idle_cap_no_regroup(self, idle_capacity_ton):
        """Add idle capacity passed in ton-km, that can not be removed."""
        self.idle_capacity_no_regroup += idle_capacity_ton

    def get_idle_cap(self):
        """Returns idle capacity in tons."""
        return self.idle_capacity_regroup + self.idle_capacity_no_regroup

    def get_idle_cap_tk(self):
        """Returns idle capacity in ton-km."""
        return self.get_idle_cap() * self.dist

    def get_idle_cap_regroup_tk(self):
        """Returns idle capacity in ton-km, that can be removed."""
        return self.idle_capacity_regroup * self.dist

    def get_idle_cap_no_regroup_tk(self):
        """Returns idle capacity in ton-km, that can not be removed."""
        return self.idle_capacity_no_regroup * self.dist

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
                      self.get_idle_cap()) / locomotive_capacity
        locoms_weight = num_locoms * locomotive_weight

        # calculate gross ton-km
        self.gross_tk = (wagons_weight + locoms_weight +
                         self.get_ton()) * self.dist

        return self.gross_tk

    def get_number_of_detours(self):
        """Calculate number of detours needed at the link."""

        # check if there is traffic
        if self.gross_tk:
            num_detours = self._calc_number_of_detours(self.gross_tk,
                                                       self.get_dist())
        else:
            num_detours = 0

        return num_detours

    # PRIVATE
    def _calc_number_of_detours(self, gross_tk, dist):
        """Calculate number of detours needed in a certain track."""

        # store parameters in short-name variables
        max_turnout_distance = self.turnout_freq
        max_turnout_density = self.turnout_freq_max_density
        t_distance = max_turnout_distance

        # calculate density
        density = gross_tk / dist

        if not density < max_turnout_density:
            t_distance = max_turnout_distance / (density / max_turnout_density)

        num_detours = dist / t_distance

        return num_detours


def test():

    print "\nCreate a link"
    print "-----------"
    link = RailwayLink("1009-1003", 150.4, "ancha")

    print link

if __name__ == '__main__':
    test()
