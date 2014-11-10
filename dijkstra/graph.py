#!C:\Python27
# -*- coding: utf-8 -*-

class Graph(dict):

    def __init__(self, ws):
        self._build_graph(ws)

    # toma el "self" de una tabla en excel
    def _build_graph(self, ws):
        
        # ArchivoExcel: debe proporcionarse la ruta entera del excel
        
        # HojaNodos: debe proporcionarse el nombre de la hoja donde esta la lista de nodos de la red.
            # Deben estar en el rango ("A2:A ")
        
        # HojaAdyacencias: debe proporcionarse el nombre de la hoja con la lista de adyacencias y weights
            # Columnas A: Nodo que se releva / B: Nodos adyacentes al A / C: Distancia entre A y B
        
        # HojaOutput: nombre de la hoja donde saldra el output
            # Columnas A: Par OD / B: Nodo origen / C: Nodo destino / D: Distancia / E: Ruta
        
        #inicializa las celdas a utilizar en la carga del grafo
        cell_node_a = ws.cell(column = 1, row = 2)
        cell_node_b = ws.cell(column = 2, row = 2)
        cell_weight = ws.cell(column = 3, row = 2)
        
        #carga los datos al self
        while cell_node_a.value:
            
            # almacena los datos de la primera vila
            node_a = cell_node_a.value
            node_b = cell_node_b.value
            weight = cell_weight.value
            
            # adds link in both ways (a to b, b to a)
            self._add_link(node_a, node_b, weight)
            self._add_link(node_b, node_a, weight)
                
            # print "Nuevo registro:  " + str(node_a) + "  " + str(node_b) + "  " + str(weight)
            
            # se mueve a la siguiente fila de la tabla
            cell_node_a = cell_node_a.offset(row = 1, column = 0)
            cell_node_b = cell_node_b.offset(row = 1, column = 0)
            cell_weight = cell_weight.offset(row = 1, column = 0)


    def _add_link(self, node_a, node_b, weight):
        """Add a node a to the graph with a weighted link with node b"""

        # create weighted link as a tuple
        print node_b, weight
        weighted_link = (node_b, float(weight))

        # create node_a if not already in graph
        if not node_a in self:
            self[node_a] = []
        
        # add link to node_a if not already present
        if not weighted_link in self[node_a]:
            self[node_a].append(weighted_link)