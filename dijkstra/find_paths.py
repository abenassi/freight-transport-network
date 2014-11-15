#!C:\Python27
# -*- coding: utf-8 -*-
import sys
import time
from openpyxl import load_workbook
from modules import dijkstra, Graph


class Network():

    NETWORK_NAMES = ["ancha", "media", "angosta"]
    PATH_SHEET_SUFFIX = "recorridos"
    XL_OUTPUT = "Calculo recorridos para red ffcc.xlsx"
    PATH_FIELDS = ["id_od", "origen", "destino", "distancia", "ruta"]
    NETWORK_TYPE_NAME = "trocha"

    def __init__(self, network_names=None):
        """Init with network names of the railway network."""

        self.network_names = network_names or self.NETWORK_NAMES
        self.graphs = {}
        self.paths = {}

    # PUBLIC
    def create_graphs_from_excel(self, wb):
        """Create graphs from network worksheets provided."""

        # iterate through each network_name and worksheet
        for network_name in self.network_names:

            # take worksheet
            ws = wb.get_sheet_by_name(network_name)

            # create graph
            self.graphs[network_name] = Graph(ws)

    def calculate_paths(self):

        # start total networks timer
        total_timer_start = time.time()

        # iterate through each network_name
        for network_name in self.network_names:

            # start network timer
            network_timer_start = time.time()

            # calculate paths for the network
            self._calculate_paths(network_name)

            # stop network timer
            elapsed = (time.time() - network_timer_start)
            self._report_time(elapsed, network_name)
            print "\n"

        # stop total networks timer
        elapsed = (time.time() - total_timer_start)
        self._report_time(elapsed, "all networks")

    def store_paths_in_excel(self, wb, xl_output=None):

        print "\n Saving results in excel..."
        sys.stdout.flush()

        # create worksheet to store all results
        ws_all = wb.create_sheet()
        ws_all.title = self.PATH_SHEET_SUFFIX

        # write field names
        fields = list(self.PATH_FIELDS)
        fields.append(self.NETWORK_TYPE_NAME)
        ws_all.append(fields)

        # store paths for each network
        for network_name in self.paths:
            self._store_network_paths(wb, network_name, ws_all)

        # sort by distance before save
        # self._sort_by_distance(ws_all)

        # save workbook
        wb.save(xl_output or self.XL_OUTPUT)

        print "Finished."

    # PRIVATE
    def _calculate_paths(self, network_name):

        # take graph of network
        graph = self.graphs[network_name]

        # create paths dictionary
        self.paths[network_name] = {}
        paths = self.paths[network_name]

        # take nodes
        nodes = graph.keys()
        nodes.sort()

        # calcualte total paths
        total_paths = len(nodes) ** 2
        print total_paths, "paths will be calculated"

        # calculate minimum paths between all nodes
        index_calculated_paths = 0
        start_timer = time.time()

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

                else:

                    # use dijkstra to calculate minimum path from a to b
                    distance, path = dijkstra(graph, node_a, node_b)

                    # replace "a" in path for node_a
                    path[0] = node_a

                    # store results in paths
                    paths[node_a][node_b]["distance"] = distance
                    paths[node_a][node_b]["path"] = path

                # show progress
                index_calculated_paths += 1

                elapsed = (time.time() - start_timer)

                activity = str(index_calculated_paths) + \
                           " paths calculation from " + \
                           str(total_paths) + " total paths "

                # self._report_time(elapsed, activity)

    def _report_time(self, time_spend, activity):
        print "{} took {:.2} seconds".format(activity, time_spend)

    def _store_network_paths(self, wb, network_name, ws_all=None):

        # create worksheet and write field names
        ws = wb.create_sheet()
        ws.title = network_name + "_" + self.PATH_SHEET_SUFFIX
        ws.append(self.PATH_FIELDS)

        # take paths of the network_name
        paths = self.paths[network_name]

        # take nodes to iterate
        nodes = sorted(paths.keys())

        # iterate throught paths, copying them to worksheet
        for node_a in nodes:
            for node_b in nodes:

                # take distance
                distance = paths[node_a][node_b]["distance"]

                # create string por path
                list_path = paths[node_a][node_b]["path"]

                if list_path:
                    list_path = [str(node).zfill(3) for node in list_path]
                    string_path = "-".join(list_path)

                else:
                    string_path = None

                # create link name
                link_name = str(node_a) + "-" + str(node_b)

                # copy data to worksheet
                data = [link_name, node_a, node_b, distance, string_path]
                ws.append(data)

                # copy data to global worksheet
                if ws_all:
                    data.append(network_name)
                    ws_all.append(data)

    def _sort_by_distance(ws):
        pass


def calculate_paths_from_excel(wb, network_names=None, xl_output=None):

    network = Network(network_names)

    network.create_graphs_from_excel(wb)
    network.calculate_paths()
    network.store_paths_in_excel(wb, xl_output)

    return network


def main(xl_input, network_names, xl_output):

    wb = load_workbook(xl_input)
    calculate_paths_from_excel(wb, network_names, xl_output)


def main_railway():

    XL_INPUT = "data/railway_links_table.xlsx"
    NETWORK_NAMES = ["ancha", "media", "angosta"]
    XL_OUTPUT = "paths/railway_shortest_paths.xlsx"
    main(XL_INPUT, NETWORK_NAMES, XL_OUTPUT)


def main_roadway():

    XL_INPUT = "data/roadway_links_table.xlsx"
    NETWORK_NAMES = ["unica"]
    XL_OUTPUT = "paths/roadway_shortest_paths.xlsx"
    main(XL_INPUT, NETWORK_NAMES, XL_OUTPUT)


if __name__ == "__main__":

    if len(sys.argv) == 4:

        xl_input = sys.argv[1]
        network_names = sys.argv[2].split("-")
        xl_output = sys.argv[3]

        main(xl_input, network_names, xl_output)

    else:

        main_railway()
        main_roadway()
