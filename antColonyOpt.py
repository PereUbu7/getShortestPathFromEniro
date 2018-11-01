import math

from aco import ACO, Graph
from plot import plot


def main():
    cities = ["Kvarnfors gård 7 Gustafs", "Österbo 115 Falun", "Borganäsvägen Borlänge", "Slaggatan 2 Falun"]
    points = []

    cost_matrix = [[0, 20, 17, 26], [20, 0, 25, 16], [13, 24, 0, 13], [25, 16, 13, 0]]
    rank = len(cities)

    aco = ACO(10, 100, 1.0, 10.0, 0.5, 10, 2, True)
    graph = Graph(cost_matrix, rank)
    path, cost = aco.solve(graph)
    print('cost: {}, path: {}'.format(cost, path))
