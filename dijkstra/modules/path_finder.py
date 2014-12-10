from dijkstra import dijkstra


class IsolatedGaugesStrategy(object):

    """Find paths without transshipments between gauges."""

    # PUBLIC
    def find_shortest_paths(self, graphs, restrictions=None):
        """Find shortest paths for each possible pair of nodes, by gauge."""

        paths = {}

        gauge_names = graphs.keys()
        for gauge in gauge_names:

            # prepare graph removing restrictions
            graph = graphs[gauge]
            self._remove_restricted_nodes_and_links(graph, restrictions)

            # find shortest path for the gauge
            gauge_paths = self._find_shortest_paths(gauge, graph)
            paths[gauge] = gauge_paths

        return paths

    def find_shortest_path(self, node_a, node_b, graphs, restrictions=None):
        """Find shortest paths for each possible pair of nodes, by gauge."""

        paths = {}

        gauge_names = graphs.keys()
        for gauge in gauge_names:

            # prepare graph removing restrictions
            graph = graphs[gauge]
            self._remove_restricted_nodes_and_links(graph, restrictions)

            # find shortest path for the gauge
            if (node_a in graph) and (node_b in graph):

                distance, path = dijkstra(graph, node_a, node_b)
                paths[gauge] = {}
                paths[gauge]["distance"] = distance
                paths[gauge]["path"] = path

        return paths

    # PRIVATE
    def _find_shortest_paths(self, gauge, graph):
        """Find shortest paths for each possible pair of nodes.

        Args:
            gauge: Name of the gauge to calculate shortest paths.
        """
        paths = {}

        # get nodes with access to the gauge
        nodes = graph.keys()
        nodes.sort()

        # calcualte total paths
        total_paths = len(nodes) ** 2
        print total_paths, "paths will be calculated"

        for node_a in nodes:

            # create dictionary for node a in paths
            paths[node_a] = {}

            for node_b in nodes:

                # create dictionary for node b in node a
                paths[node_a][node_b] = {}

                # if is the same node, there is no path
                if node_a == node_b:

                    paths[node_a][node_b]["distance"] = 0.0
                    paths[node_a][node_b]["path"] = None

                # if nodes are different, find shortest path
                else:

                    # use dijkstra to calculate minimum path from a to b
                    distance, path = dijkstra(graph, node_a, node_b)

                    # store results in paths
                    paths[node_a][node_b]["distance"] = distance
                    paths[node_a][node_b]["path"] = path

        return paths

    def _remove_restricted_nodes_and_links(self, graph, restrictions):
        """Remove restricted nodes and links that use them from graph.

        Args:
            graph: Graph dictionary with nodes as keys and lists of links as
                values.
            restrictions: List of nodes (eg. "a") or links (eg. ("a", "b"))
                that are not to be used calculating paths.
        """

        # exit the method if none restrictions are passed
        if not restrictions:
            return

        for node in graph.keys():

            # check if node is restricted
            if node in restrictions:
                del graph[node]

            # check if links are restricted
            else:
                for edge in graph[node]:

                    has_restricted_node = (node == edge[0])

                    link_a = (node, edge[0])
                    link_b = (edge[0], node)
                    is_restricted_link = (link_a in restrictions or
                                          link_b in restrictions)

                    if has_restricted_node or is_restricted_link:
                        graph[node].remove(edge)


class MultipleGaugesStrategy(object):

    """Find paths with transshipments between gauges."""

    def find_shortest_paths(self, graphs, argument):
        """Find shortest paths for each possible pair of nodes, by gauge."""
        pass

    def _find_multiple_gauges_shortest_paths_maxt(self, max_transshipments):
        """Find shortest paths allowing transshipments between gauges.

        Args:
            max_transshipments: Maximum number of transshipments between
                different gauges allowed.
        """
        pass

    def _find_multiple_gauges_shortest_paths_costt(self, cost_transshipments):
        """Find shortest paths allowing transshipments between gauges.

        Args:
            cost_transshipments: Cost in terms of "distance" to apply when
                changing between gauges in a path.
        """
        pass


STRATEGIES = {"isolated_gauges": IsolatedGaugesStrategy,
              "multiple_gauges": MultipleGaugesStrategy}


def get_path_finder_strategy(strategy_name):
    return STRATEGIES[strategy_name]()
