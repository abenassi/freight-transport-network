class BaseOptimizationStrategy(object):

    ALLOW_ORIGINAL = False

    def __init__(self, fn):
        self.fn = fn

    def _cost_has_increased(self, old_cost):
        self.fn.cost_network()
        new_cost = self.fn.total_cost

        return new_cost > old_cost

    def _get_total_cost(self):
        self.fn.cost_network()

        return self.fn.total_cost


class BaseDerivationStrategy(BaseOptimizationStrategy):

    """docstring for BaseDerivationStrategy"""

    def _revert_derivations(self, deriv_ods):
        for road_od in deriv_ods:
            self.fn.derive.od_to_railway(road_od)


class BaseReroutingStrategy(BaseOptimizationStrategy):

    """docstring for BaseReroutingStrategy"""

    def _revert_reroutings(self, rerouted_ods):
        for rail_od in rerouted_ods:
            self.fn.reroute.revert_reroute_od(self.fn.rail, rail_od)


class LinksTrafficRerouter(BaseDerivationStrategy, BaseReroutingStrategy):

    """docstring for LinksTrafficRerouter   """

    def optimize(self):

        for rail_link in self.fn.iter_rail_links(sorted_by=True):

            # only check links that has more than zero tons
            if rail_link.tons.get() > 0.0:

                print "Analyzing rerouting of", rail_link,

                old_cost = self._get_total_cost()

                # reroute (or derive, if impossible) all od pairs using a link
                rail_link_id = rail_link.id
                rail_link_gauge = rail_link.gauge
                res = self.fn.reroute.reroute_link(rail_link_id,
                                                   rail_link_gauge,
                                                   self.ALLOW_ORIGINAL)
                rerouted_ods, deriv_ods = res

                if self._cost_has_increased(old_cost):
                    self._revert_derivations(deriv_ods)
                    self._revert_reroutings(rerouted_ods)
                    print "...ok."

                else:
                    print "...REROUTED!"


class WeakLinksAggregator(BaseDerivationStrategy):

    def optimize(self):

        for rail_link in self.fn.iter_rail_links(sorted_by=True):

            # only check links that has more than zero tons
            if rail_link.tons.get() > 0.0:

                print "Analyzing derivation of", rail_link,

                old_cost = self._get_total_cost()

                # derive all od pairs of a link to roadway network
                rail_link_id = rail_link.id
                rail_link_gauge = rail_link.gauge
                deriv_ods = self.fn.derive.link_to_roadway(rail_link_id,
                                                           rail_link_gauge,
                                                           self.ALLOW_ORIGINAL)

                if self._cost_has_increased(old_cost):
                    self._revert_derivations(deriv_ods)
                    print "...ok."

                else:
                    print "...DERIVED BACK TO ROADWAY!"


class WeakOdsAggregator(BaseDerivationStrategy):

    def optimize(self):

        for rail_od in self.fn.iter_rail_ods(sorted_by=True):

            # only check links that has more than zero tons
            if rail_od.tons.get() > 0.0:

                print "Analyzing derivation of", rail_od,

                old_cost = self._get_total_cost()

                # derive rail od pair to roadway mode
                road_od = self.fn.derive.od_to_roadway(rail_od, None,
                                                       self.ALLOW_ORIGINAL)
                deriv_ods = [road_od]

                if self._cost_has_increased(old_cost):
                    self._revert_derivations(deriv_ods)
                    print "...ok."

                else:
                    print "...DERIVED BACK TO ROADWAY!"
