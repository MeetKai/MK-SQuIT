# Copyright (c) 2020 MeetKai Inc. All rights reserved.

import random
from typing import List, Tuple

import typer
import networkx as nx

from mk_squit.generation.predicate_bank import PredicateBank


class TypeGenerator(object):
    """Generate predicate chains intelligently by traversing a graph made from predicate types."""

    def __init__(self, predicate_bank: PredicateBank):
        self.predicate_bank = predicate_bank

        # G and Gi are directed graphs with edges in opposite directions
        G = nx.DiGraph()
        Gi = nx.DiGraph()

        for e in list(self.predicate_bank.bank.keys()):
            ns = e.split("->")
            G.add_edge(*ns)
            G[ns[0]][ns[1]]["label"] = e

            ns.reverse()
            Gi.add_edge(*ns)
            Gi[ns[0]][ns[1]]["label"] = e

        # nx.draw_shell(G, with_labels=True, font_weight='bold')
        # plt.show()

        self.G = G
        self.Gi = Gi

    def generate_unidirectional_pred_traversal(
        self, graph: nx.DiGraph, node: str, steps: int, init: bool = True
    ) -> List[Tuple[List[str], str]]:
        """
        Args:
            graph: An nx.DiGraph with nodes as thing types and edges as predicate types
            node: "person"
            steps: 2
            init: False
        Returns:
            A list of graph traversals of length steps and the node type that the traversal ends on
            [(['person->person', 'person->country'], 'country'), ...]
        """
        if steps == 0:
            if init:
                return [[[], node]]
            return [[node]]
        paths = []
        for neighbor in graph.neighbors(node):
            for path in self.generate_unidirectional_pred_traversal(graph, neighbor, steps - 1, False):
                paths.append([node] + path)
        if not init:
            return paths
        else:
            edge_labels = []
            for path in paths:
                traversals = []
                for i in range(steps):
                    traversals.append(graph.get_edge_data(path[i], path[i + 1])["label"])
                edge_labels.append(traversals)
            return list(zip(edge_labels, [path[-1] for path in paths]))

    def generate_bidirectional_pred_traversal(
        self,
        start: str,
        end: str,
        forward_traversal_length: int,
        backward_traversal_length: int,
        graph: nx.DiGraph,
        anti_graph: nx.DiGraph,
        debug_stats: bool = False,
    ) -> (List[str], List[str]):
        """
        Args:
            start: 'person'
            end: 'movie'
            forward_traversal_length: 2
            backward_traversal_length: 1
            graph: An nx.DiGraph
            anti_graph: An nx.DiGraph
            debug_stats: False

        Returns:
            A bidirectional traversal with the given start and end points and traversal lengths
        """
        forward_traversals = self.generate_unidirectional_pred_traversal(graph, start, forward_traversal_length)
        random.shuffle(forward_traversals)

        all_paths = None

        if debug_stats:
            all_paths = []

        for forward_traversal in forward_traversals:
            # We exclude some thing types for the Multi-Entity query
            if forward_traversal[1] in [
                "text",
                "id",
                "thing",
                "image",
                "television_series",
                "literary_work",
                "movie",
                "url",
                "rating",
            ]:
                continue
            backward_traversals = self.generate_unidirectional_pred_traversal(
                anti_graph, forward_traversal[1], backward_traversal_length
            )
            random.shuffle(backward_traversals)
            for backward_traversal in backward_traversals:
                if backward_traversal[1] == end:
                    backward_traversal[0].reverse()
                    if debug_stats:
                        all_paths.append((forward_traversal[0], backward_traversal[0]))
                    else:
                        return forward_traversal[0], backward_traversal[0]
        return all_paths


def example(data_dir: str = "data", prop_id: str = "*-props-preprocessed.json", ent_id: str = "*-5k-preprocessed.json"):
    """TypeGenerator example functionality.

    python -m mk_squit.generation.type_generator \
        --data-dir data \
        --prop-id *-props-preprocessed.json \
        --ent-id *-5k-preprocessed.json
    """
    pb = PredicateBank(data_dir=data_dir, property_file_identifier=prop_id, entity_file_identifier=ent_id)
    type_gen = TypeGenerator(pb)
    print(type_gen.generate_unidirectional_pred_traversal(type_gen.G, "person", 2))
    print(random.choice(list(type_gen.generate_unidirectional_pred_traversal(type_gen.G, "person", 2)))[0])
    print(type_gen.generate_bidirectional_pred_traversal("television_series", "person", 2, 2, type_gen.G, type_gen.Gi))


if __name__ == "__main__":
    typer.run(example)
