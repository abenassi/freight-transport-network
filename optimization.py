class OptimizationStrategy():

    def __init__(self, fn):
        self.fn = fn

    def optimize(self):
        pass


class WeakLinksAggregator(OptimizationStrategy):

    def optimize(self):

        for rail_link in self.fn.iter_rail_links():

            # only check links that has more than zero tons
            if rail_link.get_ton() > 0.0:

                print "Analyzing derivation of", rail_link,

                # store current network cost
                self.fn.cost_network()
                curr_cost = self.fn.get_total_cost()

                # derive all od pairs of a link to roadway network
                derivations = self.fn.derive_link_to_roadway(rail_link.get_id(),
                                                             rail_link.get_gauge())

                # revert derivation if overall cost has increased
                self.fn.cost_network()
                new_cost = self.fn.get_total_cost()
                if new_cost > curr_cost:
                    self._revert_derivations(derivations)
                    print "...reverted."

                else:
                    print "...DERIVED!"

    def _revert_derivations(self, derivations):

        for road_od in derivations:
            self.fn.derive_to_railway(road_od)
