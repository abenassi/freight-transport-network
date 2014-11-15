def dijkstra(graph, a, z):
    """
    Algoritmo de Dijkstra

    Determina el camino mas corto entre los vertices 'a' y 'z' de un
    grafo ponderado y conexo 'graph'.
    """
    assert a in graph
    assert z in graph

    # Definicion de infinito como un valor mayor 
    # al doble de suma de todos los pesos
    Inf = 0
    for u in graph:
        for v, w in graph[u]:
            Inf += w

    # Inicializacion de estructuras auxiliares:
    #  L: diccionario vertice -> etiqueta
    #  S: conjunto de vertices con etiquetas temporales
    #  A: vertice -> vertice previo (en camino longitud minima)
    L = dict([(u, Inf) for u in graph]) #py3: L = {u:Inf for u in graph}
    L[a] = 0
    S = set([u for u in graph]) #py3: S = {u for u in graph}
    A = { }

    # Funcion auxiliar, dado un vertice retorna su etiqueta
    # se utiliza para encontrar el vertice the etiqueta minima
    def W(v):
        return L[v]
    # Iteracion principal del algoritmo de Dijkstra
    while z in S:
        u = min(S, key=W)
        S.discard(u)
        for v, w in graph[u]:
            if v in S:
                if L[u] + w < L[v]:
                    L[v] = L[u] + w
                    A[v] = u

    # Reconstruccion del camino de longitud minima
    P = []
    u = z
    while u != a:
        P.append(u)
        u = A[u]
    P.append('a')
    P.reverse()

    # retorna longitud minima y camino de longitud minima
    return L[z], P
                    

G1 = { # Rosen, Figura 4 (pp. 559)
    'a' : [('b', 4), ('c',2)],
    'b' : [('a', 4), ('c',1), ('d',5)],
    'c' : [('a', 2), ('b',1), ('d',8), ('e',10)],
    'd' : [('b', 5), ('c',8), ('e',2), ('z', 6)],
    'e' : [('c',10), ('d',2), ('z',3)],
    'z' : [('d', 6), ('e',3)],
    }

G2 = { # Rosen, Ej. 8.6-2 (pp. 562)
    'a' : [('b', 2), ('c',3)],
    'b' : [('a', 2), ('d',5), ('e',2)],
    'c' : [('a', 3), ('e',5)],
    'd' : [('b', 5), ('e',1), ('z',2)],
    'e' : [('b', 2), ('c',5), ('d',1), ('z',4)],
    'z' : [('d', 2), ('e',4)],
    }


def test():
    
    from pprint import pprint
    #
    w, p =  dijkstra(G1, 'a', 'z')
    pprint (G1)
    pprint (p)
    pprint (w)
    #
    w, p =  dijkstra(G2, 'a', 'z')
    pprint (G2)
    pprint (p)
    pprint (w)

if __name__ == '__main__':
    test()
