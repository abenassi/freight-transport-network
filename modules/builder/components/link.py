from tons import LinkTons


class BaseLink(object):

    """Base class for a link in a freight transport network."""

    def __init__(self, id, distance, gauge):

        # identification properties
        self.id = id
        self.id_gauge = id + "_" + gauge
        self.gauge = gauge
        self.nodes = [int(i) for i in id.split("-")]

        # static properties
        self.dist = float(distance)  # Km

        # traffic parameters
        self._main_track = None

        # track costs
        self.eac_track = None
        self.maintenance = None

        # other parameters
        self.net_to_gross_factor = None

        self.tons = LinkTons()

    def __repr__(self):
        return "Link: " + str(self.id).ljust(10) + \
               "Distance: {:,.1f}".format(self.dist).ljust(18) + \
               "Gauge: " + str(self.gauge).ljust(8) + \
               "Ton: {:,.1f}".format(self.tons.get()).ljust(20)

    def __len__(self):
        return self.dist

    def __lt__(self, other):
        return self.tons.get() < other.tons.get()

    @property
    def ton_km(self):
        """Calculates ton-km being transported in a link.

        >>> link = BaseLink("1-3", 100.0, "ancha")
        >>> link.tons.add_original(10.0, 1, "1-3")
        >>> link.ton_km
        1000.0
        """
        return self.tons.get() * self.dist

    @property
    def gross_ton_km(self):
        """Calculates gross ton-km being transported in a link.

        >>> link = BaseLink("1-3", 100.0, "ancha")
        >>> link.tons.add_original(10.0, 1, "1-3")
        >>> link.net_to_gross_factor = 2
        >>> link.gross_ton_km
        2000.0
        """
        return self.ton_km * self.net_to_gross_factor

    @property
    def main_track(self):
        return self._main_track

    @main_track.setter
    def main_track(self, main_track):
        """Set track category between main (A) and secondary (B)."""
        if main_track:
            self._main_track = "A"
        else:
            self._main_track = "B"

    # others
    def reset(self):
        self.eac_track = None
        self.maintenance = None

        # check stored values of tons are significant
        self.tons.clean_insignificant_ton_values(0.01)


class RoadwayLink(BaseLink):

    """Represents a link in a roadway network.

    TODO: It still needs to be implemented, for the moment RailwayLink is
    used as its good enough to act as a RoadwayLink as it is."""

    FIELDS = ["id_link", "gauge", "distance", "original_tons", "derived_tons",
              "tons", "gross ton-km"]

    def get_attributes(self):
        return [self.id, self.gauge, self.dist, self.tons.get_original(),
                self.tons.get_derived(), self.tons.get(),
                self.gross_ton_km]


class RailwayLink(BaseLink):

    """Represents a link in a railway network.

    It keeps track of tons passing and idle capacity of tons that could be
    supported with the same rolling material currently running."""

    FIELDS = ["id_link_gauge", "id_link", "gauge", "distance", "original_tons",
              "derived_tons",
              "tons", "idle_capacity_regroup", "idle_capacity_no_regroup",
              "turnout_cost", "track_cost", "maintenance_cost", "gross ton-km",
              "num_turnouts", "track_type", "category_1", "category_2",
              "category_3", "category_4", "category_5", "net_to_gross_factor"]

    def __init__(self, id, distance, gauge):

        # call superclass constructor first
        super(RailwayLink, self).__init__(id, distance, gauge)

        # traffic parameters
        self.idle_capacity_regroup = 0.0
        self.idle_capacity_no_regroup = 0.0
        self.regrouped = False

        # turnout parameters
        self.turnout_freq = None
        self.turnout_freq_max_density = None

        # track costs
        self.eac_turnout = None

    def __repr__(self):
        return "Link: " + str(self.id).ljust(10) + \
               "Distance: {:,.1f}".format(self.dist).ljust(18) + \
               "Gauge: " + str(self.gauge).ljust(8) + \
               "Ton: {:,.1f}".format(self.tons.get()).ljust(20) + \
               "Idle capacity: {:,.1f}".format(self.idle_capacity).ljust(30)

    # PUBLIC
    # getters
    def get_attributes(self):
        return [self.id_gauge, self.id, self.gauge, self.dist,
                self.tons.get_original(),
                self.tons.get_derived(), self.tons.get(),
                self.idle_capacity_regroup,
                self.idle_capacity_no_regroup, self.eac_turnout,
                self.eac_track, self.maintenance, self.gross_ton_km,
                self.number_of_turnouts,
                self.main_track] + self.tons.get_by_category() + [self.net_to_gross_factor]

    @property
    def idle_capacity(self):
        """Returns idle capacity in tons."""
        return self.idle_capacity_regroup + self.idle_capacity_no_regroup

    @property
    def idle_capacity_tk(self):
        """Returns idle capacity in ton-km."""
        return self.idle_capacity * self.dist

    @property
    def idle_capacity_regroup_tk(self):
        """Returns idle capacity in ton-km, that can be removed."""
        return self.idle_capacity_regroup * self.dist

    @property
    def idle_capacity_no_regroup_tk(self):
        """Returns idle capacity in ton-km, that can not be removed."""
        return self.idle_capacity_no_regroup * self.dist

    @property
    def gross_ton_km(self):
        """Calculate gross ton-km of a railway link.

        Overrides super class method to take into account idle capacity."""

        if self.tons.get() and self.tons.get() > 0.0:

            gross_ton = (self.tons.get() * self.net_to_gross_factor)

            gross_tk = gross_ton * self.dist

        else:
            gross_tk = 0.0

        return gross_tk

    @property
    def number_of_turnouts(self):
        """Calculate number of turnouts needed at the link."""

        # check if there is traffic
        if self.gross_ton_km > 0.1:
            num_turnouts = self._calc_number_of_turnouts(self.gross_ton_km,
                                                         self.dist)
        else:
            num_turnouts = 0

        return num_turnouts

    # regroup methods
    def regroup(self, idle_capacity_ton):
        """Eliminate idle capacity passed in ton."""

        # check if link has that idle capacity
        if self.idle_capacity_regroup - idle_capacity_ton < 0:
            msg = "{} has no {} idle capacity!".format(self.id,
                                                       idle_capacity_ton)

            raise ValueError(msg)

        self.idle_capacity_regroup -= idle_capacity_ton
        self.regrouped = True

    def revert_regroup(self, idle_capacity_ton):
        """Regain idle capacity passed in ton."""
        self.idle_capacity_regroup += idle_capacity_ton
        self.regrouped = False

    def reset(self):
        self.eac_track = None
        self.maintenance = None

        self.idle_capacity_regroup = 0.0
        self.idle_capacity_no_regroup = 0.0
        self.eac_turnout = 0.0
        self.regrouped = False

        # check stored values of tons are significant
        self.tons.clean_insignificant_ton_values(0.01)

    # PRIVATE
    def _calc_number_of_turnouts(self, gross_tk, dist):
        """Calculate number of turnouts needed in a certain track."""

        # store parameters in short-name variables
        max_turnout_distance = self.turnout_freq
        max_turnout_density = self.turnout_max_density
        t_distance = max_turnout_distance

        # calculate density
        density = gross_tk / dist

        if not density < max_turnout_density:
            t_distance = max_turnout_distance / (density / max_turnout_density)

        num_turnouts = dist / t_distance

        return num_turnouts


if __name__ == '__main__':

    import doctest
    doctest.testmod()
