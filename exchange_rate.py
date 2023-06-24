import operator
from functools import reduce

import matplotlib.pyplot as plt
import networkx as nx
from icecream import ic


def construct_graph(given_pairs):
    graph = nx.DiGraph()
    for currency_from, currency_to, rate in given_pairs:
        graph.add_nodes_from((currency_from, currency_to))
        graph.add_edge(currency_from, currency_to, rate=rate)
        graph.add_edge(currency_to, currency_from, rate=1/rate)
    return graph


def compute_all_rates(given_pairs):
    """
    Given a set of exchange rates, compute all possible exchange rates
    both explicit and implicit rates
    """
    graph = construct_graph(given_pairs)

    paths = {currency: nx.single_source_dijkstra_path(graph, currency) for currency in graph.nodes()}

    def compute_path_rate(path):
        if len(path) == 1:
            return 1
        else:
            tuples = zip(path[:-1], path[1:])
            return reduce(operator.mul, [graph.get_edge_data(u, v)['rate'] for u, v in tuples])

    rates = {u: {v: compute_path_rate(paths[u][v]) for v in paths[u].keys()} for u in paths.keys()}
    return rates


def plot_graph(given_pairs):
    graph = construct_graph(given_pairs)
    pos = nx.circular_layout(graph)

    def edge_text(u, v):
        rate_1 = graph.edges[(u, v)]["rate"]
        rate_2 = graph.edges[(v, u)]["rate"]
        return f'{rate_1}\n\n{rate_2}'
    edge_labels = dict([((u, v,), edge_text(u, v)) for u, v, d in graph.edges(data=True) if pos[u][0] > pos[v][0]])
    # edge_labels = dict([((u, v,), d["rate"]) for u, v, d in graph.edges(data=True) if pos[u][0] > pos[v][0]])
    nx.draw_networkx(graph, pos, with_labels=True, connectionstyle='arc3, rad = 0.1')
    nx.draw_networkx_edge_labels(graph, pos, edge_labels=edge_labels, rotate=False)
    plt.axis('off')
    plt.show()


if __name__ == '__main__':
    example = [
        ('A', 'B', 2),
        ('B', 'C', 4),
    ]
    ic(compute_all_rates(example))
    plot_graph(example)
