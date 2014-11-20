def dijkstra(graph, node_a, node_z):
    """
    Implementation of dijkstra shortest path algorithm.

    Find the shortest path between vertex 'a' and 'z' from a weighted graph
    with links.

    Args:
        graph: Dictionary-like Graph with all the nodes and its weighted links.
        node_a: Node of origin.
        node_z: Node of destination.
    """

    # check nodes are in graph
    assert node_a in graph
    assert node_z in graph

    # infinite will be the sum of all weights
    inf = 0
    for node in graph:
        for link, weight in graph[node]:
            inf += weight

    # set initial distances to node_a of all nodes as infinite
    node_distances = dict([(node, inf) for node in graph])

    # set distance of node_a to itself to zero
    node_distances[node_a] = 0

    # create a set with all nodes in the graph
    nodes_set = set([node for node in graph])

    # create a dictionary that will have the previous vertix of each node
    previous_vertix = {}

    # aux method to get distance of a certain vertix to node_a
    def get_distance(vertix):
        return node_distances[vertix]

    # main iteration of dijkstra algorithm
    while node_z in nodes_set:

        # get node with minimum distance from the set of nodes
        node = min(nodes_set, key=get_distance)

        # remove selected node from the set
        nodes_set.discard(node)

        # iterate through vertices of the selected node
        for vertix, weight in graph[node]:

            # check if vertix is in the set
            if vertix in nodes_set:

                # check if path through this vertix would be shorter
                if node_distances[node] + weight < node_distances[vertix]:

                    # update distance of vertix with the shorter one found
                    node_distances[vertix] = node_distances[node] + weight

                    # update the previous_vertix to be the new closer node
                    previous_vertix[vertix] = node

    # reconstruct the path found creating a list of nodes
    path_to_z = []
    node = node_z
    while node != node_a:
        path_to_z.append(node)
        node = previous_vertix[node]
    path_to_z.append(node_a)
    path_to_z.reverse()

    # get the distance of node_z from node_a
    distance_to_z = node_distances[node_z]

    return distance_to_z, path_to_z
