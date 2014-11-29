class BaseOptimizationStrategy():

    ALLOW_ORIGINAL = False

    def __init__(self, fn):
        self.fn = fn

    def _revert_derivations(self, deriv_ods):

        for road_od in deriv_ods:
            self.fn.derive.od_to_railway(road_od)

    def _cost_has_increased(self, old_cost):

        self.fn.cost_network()
        new_cost = self.fn.get_total_cost()

        return new_cost > old_cost

    def _get_total_cost(self):

        self.fn.cost_network()

        return self.fn.get_total_cost()


class WeakLinksAggregator(BaseOptimizationStrategy):

    def optimize(self):

        for rail_link in self.fn.iter_rail_links(sorted_by=True):

            # only check links that has more than zero tons
            if rail_link.get_ton() > 0.0:

                print "Analyzing derivation of", rail_link,

                old_cost = self._get_total_cost()

                # derive all od pairs of a link to roadway network
                rail_link_id = rail_link.get_id()
                rail_link_gauge = rail_link.get_gauge()
                deriv_ods = self.fn.derive.link_to_roadway(rail_link_id,
                                                           rail_link_gauge,
                                                           self.ALLOW_ORIGINAL)

                if self._cost_has_increased(old_cost):
                    self._revert_derivations(deriv_ods)
                    print "...ok."

                else:
                    print "...DERIVED BACK TO ROADWAY!"


class WeakOdsAggregator(BaseOptimizationStrategy):

    def optimize(self):

        for rail_od in self.fn.iter_rail_ods(sorted_by=True):

            # only check links that has more than zero tons
            if rail_od.get_ton() > 0.0:

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
