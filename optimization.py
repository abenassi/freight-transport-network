class OptimizationStrategy():

    def __init__(self, fn):
        self.fn = fn

    def optimize(self):
        pass


class WeakLinksAggregator(OptimizationStrategy):

    def optimize(self):

        for rail_link in self.fn.iter_rail_links(sorted_by=True):

            # only check links that has more than zero tons
            if rail_link.get_ton() > 0.0:

                print "Analyzing derivation of", rail_link,

                # store current network cost
                self.fn.cost_network()
                curr_cost = self.fn.get_total_cost()

                # derive all od pairs of a link to roadway network
                rail_link_id = rail_link.get_id()
                rail_link_gauge = rail_link.get_gauge()
                deriv_ods = self.fn.derive_link_to_roadway(rail_link_id,
                                                           rail_link_gauge)

                # revert derivation if overall cost has increased
                self.fn.cost_network()
                new_cost = self.fn.get_total_cost()
                if new_cost > curr_cost:
                    self._revert_derivations(deriv_ods)
                    print "...ok."

                else:
                    print "...DERIVED BACK TO ROADWAY!"

    def _revert_derivations(self, deriv_ods):

        for road_od in deriv_ods:
            self.fn.derive_to_railway(road_od)


class WeakOdsAggregator(OptimizationStrategy):

    def optimize(self):

        for rail_od in self.fn.iter_rail_ods(sorted_by=True):

            # only check links that has more than zero tons
            if rail_od.get_ton() > 0.0:

                print "Analyzing derivation of", rail_od,

                # store current network cost
                self.fn.cost_network()
                curr_cost = self.fn.get_total_cost()

                # derive rail od pair to roadway mode
                road_od = self.fn.derive_to_roadway(rail_od)

                # revert derivation if overall cost has increased
                self.fn.cost_network()
                new_cost = self.fn.get_total_cost()
                if new_cost > curr_cost:
                    self.fn.derive_to_railway(road_od)
                    print "...ok."

                else:
                    print "...DERIVED BACK TO ROADWAY!"
