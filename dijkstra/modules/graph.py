#!C:\Python27
# -*- coding: utf-8 -*-
from openpyxl import worksheet, Workbook


class Graph(dict):

    """Represents a graph (nodes with weighted links between them).

    It is built from a list of links taken from excel file. Is a subclass of
    a python dictionary where keys are all nodes of a network and values are
    lists of tuples (node_b, weight) representing the weighted links a
    particular node has.

    The representation of a network would be like this:

        {'a': [('b', 2), ('c', 3)],
         'b': [('a', 2), ('d', 5), ('e', 2)],
         'c': [('a', 3), ('e', 5)],
         'd': [('b', 5), ('e', 1), ('z', 2)],
         'e': [('b', 2), ('c', 5), ('d', 1), ('z', 4)],
         'z': [('d', 2), ('e', 4)]}
    """

    def add_edge(self, node_a, node_b, weight):
        """Add a node a to the graph with a weighted link with node b."""

        # create weighted link as a tuple
        weighted_edge = (node_b, float(weight))

        # create node_a if not already in graph
        if not node_a in self:
            self[node_a] = []

        # add link to node_a if not already present
        if not weighted_edge in self[node_a]:
            self[node_a].append(weighted_edge)


class SingleWorksheet():

    @classmethod
    def accepts(self, ws_links):
        return type(ws_links) == worksheet.worksheet.Worksheet

    def get_graphs(self, ws):
        return self._build_graph(ws)

    def _build_graph(self, ws):
        """Build graph from an excel list of links."""

        graph = Graph()

        # load first row with data of a link
        cell_node_a = ws.cell(column=1, row=2)
        cell_node_b = ws.cell(column=2, row=2)
        cell_weight = ws.cell(column=3, row=2)

        # parse data of each link into the Graph
        while cell_node_a.value:

            # store data of the row
            node_a = cell_node_a.value
            node_b = cell_node_b.value
            weight = cell_weight.value

            # adds link in both ways (a to b, b to a)
            graph.add_link(node_a, node_b, weight)
            graph.add_link(node_b, node_a, weight)

            # move on to the next row
            cell_node_a = cell_node_a.offset(row=1, column=0)
            cell_node_b = cell_node_b.offset(row=1, column=0)
            cell_weight = cell_weight.offset(row=1, column=0)

        return graph


class MultipleWorksheets():

    @classmethod
    def accepts(self, wb_links):
        return type(wb_links) == Workbook

    def get_graphs(self, wb_links):

        graphs = {}

        for ws in wb_links:
            gauge = ws.title
            graphs[gauge] = SingleWorksheet().get_graphs(ws)

        return graphs


class LinksDictionary():

    @classmethod
    def accepts(self, dict_links):
        return type(dict_links) == dict

    def get_graphs(self, dict_links):
        return self._build_graph(dict_links)


BUILDERS = [SingleWorksheet, MultipleWorksheets, LinksDictionary]


def get_graph_builder(links):

    RV = None

    for builder in BUILDERS:
        if builder.accepts(links):
            RV = builder()

    return RV
