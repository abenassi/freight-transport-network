from railway_network import RailwayNetwork
from roadway_network import RoadwayNetwork


class FreightNetwork():

    """Represents a freight network with rail and road modes of transport.

    FreightNetwork uses RailwayNetwork and RoadNetwork objects to represent a
    bimodal freight transport network. It uses those classes to cost all
    freight network and can derive traffic from one mode of transport to the
    other."""

    def __init__(self, railway_network, roadway_network):
        self.rail = railway_network
        self.road = roadway_network
        self.min_cost = sys.maxint
        self.max_cost = 0.0

    # PUBLIC
    def cost_network(self):
        """Cost total freight transport network."""
        pass

    def derive_to_railway(self, od, coeff):
        """Derive a road od pair to railway mode.

        Args:
            od: Road OD pair to be derived.
            coeff: Percentage of tons to be derived."""
        pass

    def derive_to_roadway(self, od, coeff):
        """Derive a rail od pair to roadway mode.

        Args:
            od: Rail OD pair to be derived.
            coeff: Percentage of tons to be derived."""
        pass

    def derive_all_to_railway(self):
        """Derive all possible od pairs from roadway mode to railway mode."""
        pass

    def derive_all_to_roadway(self):
        """Derive all possible od pairs from railway mode to roadway mode."""
        pass

    def free_railway_link(self, link):
        """Derive all rail OD pairs using a link to roadway mode."""
        pass

    def minimize_network_cost(self):
        """Find the modal split with minimum overall cost.

        Derive traffic from one mode to the other looking for the minimum
        overall cost of freight transportation."""
        pass

    def report_to_excel(self, add_tag=None):
        """Make a report of RailwayNetwork and RoadNetwork results.

        At any moment, freeze the status of RailwayNetwork and RoadNetwork
        into excel reports.

        Args:
            add_tag: String to be added to name of excel report, to identify
            the type of analysis being reported."""
        pass


def main():

    # initialize freight transport networks
    rail = RailwayNetwork()
    road = RoadwayNetwork()
    fn = FreightNetwork(rail, road)

    # cost network at current situation
    fn.cost_network()
    fn.report_to_excel("current situation")

    # cost network deriving all possible freight to railway
    fn.derive_all_to_railway()
    fn.cost_network()
    fn.report_to_excel("derive all to railway")

    # cost network deriving all freight to roadway
    fn.derive_all_to_roadway()
    fn.cost_network()
    fn.report_to_excel("derive all to roadway")

if __name__ == '__main__':
    main()
