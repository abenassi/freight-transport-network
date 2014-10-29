class Link():

    """Represents a link in a railway network.

    It keeps track of tons passing and idle capacity of tons that could be
    supported with the same rolling material currently running."""

    FIELDS = ["id_link", "gauge", "distance", "tons", "idle_capacity",
              "detour_cost", "track_cost", "maintenance_cost", "gross ton-km"]

    def __init__(self, id, distance, gauge):
        # identification properties
        self.id = id
        self.gauge = gauge
        self.nodes = [int(i) for i in id.split("-")]

        # static properties
        self.dist = float(distance)  # Km

        # traffic parameters
        self.ton = 0.0  # ton
        self.idle_capacity = 0.0  # ton-km

        # track costs
        self.eac_detour = None
        self.eac_track = None
        self.maintenance = None

        # gross ton-km
        self.gross_tk = None

    def __repr__(self):
        return "Link: " + str(self.id).ljust(10) + \
               "Distance: {:,.1f}".format(self.dist).ljust(18) + \
               "Gauge: " + str(self.gauge).ljust(8) + \
               "Ton: {:,.1f}".format(self.ton).ljust(15) + \
               "Idle capacity: {:,.1f}".format(self.idle_capacity)

    # PUBLIC
    def get_attributes(self):
        return [self.id, self.gauge, self.dist, self.ton, self.idle_capacity,
                self.eac_detour, self.eac_track, self.maintenance,
                self.gross_tk]

    def add_ton(self, ton):
        self.ton += ton

    def add_idle_cap(self, idle_capacity_ton):
        """Add idle capacity passed in ton."""
        self.idle_capacity += idle_capacity_ton

    def get_idle_cap(self):
        """Returns idle capacity in ton-km."""
        return self.idle_capacity * self.dist

    def regroup(self, idle_capacity_ton):
        """Eliminate idle capacity passed in ton."""

        # check if link has that idle capacity
        if self.idle_capacity - idle_capacity_ton < 0:
            raise ValueError("{} has no {} idle capacity!".format(self.id,
                                                                  idle_capacity))
        self.idle_capacity -= idle_capacity_ton

    def revert_regroup(self, idle_capacity_ton):
        """Regain idle capacity passed in ton."""
        self.idle_capacity += idle_capacity_ton

    def get_gross_ton_km(self, wagon_capacity, wagon_weight,
                         locomotive_capacity, locomotive_weight):
        """Take rolling material parameters and calculate gross ton_km."""

        # wagons weight
        num_wagons = self.ton / wagon_capacity
        wagons_weight = num_wagons * wagon_weight

        # locomotives weight
        num_locoms = (self.ton + self.idle_capacity) / locomotive_capacity
        locoms_weight = num_locoms * locomotive_weight

        return (wagons_weight + locoms_weight + self.ton) * self.dist


def test():

    print "\nTest Case 1: create a link"
    print "-----------"
    link = Link("1009-1003", 150.4, "ancha")

    print link

    print "\nTest Case 2: add tons and idle capacity"
    print "-----------"

    print "add 500 ton"
    link.add_ton(500)
    print "add 500 ton idle capacity"
    link.add_idle_cap(500)
    print link
    print "get idle cap", link.get_idle_cap()

    print "\nTest Case 3: regroup tons"
    print "-----------"

    print "regroup 250 ton of idle cap"
    link.regroup(250)
    print link
    print "get idle cap", link.get_idle_cap()

    print "\nTest Case 4: revert regroup"
    print "-----------"
    print "revert regroup 250 ton of idle cap"
    link.revert_regroup(250)
    print link
    print "get idle cap", link.get_idle_cap()

if __name__ == '__main__':
    test()
