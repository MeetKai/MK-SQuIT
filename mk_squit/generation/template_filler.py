# Copyright (c) 2020 MeetKai Inc. All rights reserved.

import re
import hashlib
from typing import List

import typer

from mk_squit.generation.predicate_bank import PredicateBank


class TemplateFiller(object):
    """Fills templates with entities and predicates from a PredicateBank."""

    def __init__(self, predicate_bank: PredicateBank):
        self.predicate_bank = predicate_bank

    def construct_query_pair(
        self, typed_template: str, pred_chain_lengths: List[int], sparql_template: str = "clauses: [CLAUSES]"
    ) -> (str, str, str):
        """
        Args:
            typed_template: "How much is the [person->weight:NOUN:A:1] of [television_series:A] 's [
                television_series->person:NOUN:A:0] ?"
            pred_chain_lengths: [2]
            sparql_template: "SELECT (COUNT(DISTINCT ?end) as ?endcount) WHERE {[CLAUSES]}"

        Returns:
            An English question and its corresponding SPARQL query, also the hash of the SPARQL query

        Generates an English - SPARQL query pair
        """

        suffixes = ["A", "B"]
        statements = []

        thing_pattern = r"\[\w+:"  # Matches [television_series:
        pred_pattern = r"\[\w+->\w+:\w+-?\w+:"  # Matches [person->weight:NOUN:

        for i in range(len(pred_chain_lengths)):
            thing_match = re.search(f"{thing_pattern}{suffixes[i]}]", typed_template)
            thing = self.predicate_bank.get_thing(thing_match.group().split(":")[0][1:])
            # thing = self.predicate_bank.get_thing("chemical")     # TEST_HARD
            typed_template = typed_template.replace(thing_match.group(), thing)
            statement = f"[ {thing} ]"

            # If there are no predicates for this chain i.e. "Who is Barack Obama?:
            if pred_chain_lengths[i] == 0:
                statement = f"BIND ( [ {thing} ] as ?end ) ."
                statements.append(statement)
                continue

            for j in range(pred_chain_lengths[i]):
                # Replace predicates in numbered order
                pred_match = re.search(f"{pred_pattern}{suffixes[i]}:{j}]", typed_template)
                pred_info = pred_match.group().split(":")
                pred = self.predicate_bank.get_predicate(pred_info[0][1:], pred_info[1])
                if pred is None:
                    return None

                prop_label, prop_wdt = pred
                typed_template = typed_template.replace(pred_match.group(), prop_label)

                # This is the first predicate
                if j == 0:
                    statement = statement + f" wdt:{prop_wdt}"
                else:
                    statement = statement + f" / wdt:{prop_wdt}"
            statement = statement + " ?end ."
            statements.append(statement)

        typed_template = typed_template.replace(" 's", "'s")
        typed_template = typed_template.replace(" ?", "?")

        # Insert the statements into the given SPARQL template
        query = sparql_template.replace("[CLAUSES]", " ".join(statements))

        unique_hash = hashlib.sha1(query.encode("utf-8"))
        unique_hex_dig = unique_hash.hexdigest()

        return typed_template, query, str(unique_hex_dig)

    def fill_single_ent_query(self, typed_template: str, trip_lengths: List[int]) -> (str, str, str):
        return self.construct_query_pair(
            typed_template, trip_lengths, sparql_template="SELECT ?end WHERE { [CLAUSES] }"
        )

    def fill_multi_ent_query(self, typed_template: str, trip_lengths: List[int]) -> (str, str, str):
        return self.construct_query_pair(typed_template, trip_lengths, sparql_template="ASK { [CLAUSES] }")

    def fill_count_query(self, typed_template: str, trip_lengths: List[int]) -> (str, str, str):
        return self.construct_query_pair(
            typed_template,
            trip_lengths,
            sparql_template="SELECT ( COUNT ( DISTINCT ?end ) as ?endcount ) WHERE { [CLAUSES] }",
        )

    def fill_query(self, key: str, typed_template: str, trip_lengths: List[int]) -> (str, str, str):
        """
        Args:
            key: "single_entity"
            typed_template: "How much is the [person->weight:NOUN:A:1] of [television_series:A] 's [
                television_series->person:NOUN:A:0] ?"
            trip_lengths: [2]
        Returns:
            An English question and its corresponding SPARQL query, also the hash of the SPARQL query
        """
        fill_function = {
            "single_entity": self.fill_single_ent_query,
            "multi_entity": self.fill_multi_ent_query,
            "count": self.fill_count_query,
        }
        return fill_function[key](typed_template, trip_lengths)


def example(data_dir: str = "data", prop_id: str = "*-props-preprocessed.json", ent_id: str = "*-5k-preprocessed.json"):
    """TemplateFiller example functionality.

    python -m mk_squit.generation.template_filler \
        --data-dir data \
        --prop-id *-props-preprocessed.json \
        --ent-id *-5k-preprocessed.json
    """
    pb = PredicateBank(data_dir=data_dir, property_file_identifier=prop_id, entity_file_identifier=ent_id)
    filler = TemplateFiller(pb)

    print(
        filler.fill_single_ent_query(
            "What is the [person->location:NOUN:A:1] of [literary_work:A] 's [literary_work->person:NOUN:A:0] ?", [2]
        )
    )
    print(
        filler.fill_multi_ent_query(
            "Is the [person->award:NOUN:A:0] of [person:A] the [person->award:NOUN:B:1] of the [person->person:NOUN:B:0] "
            "of [person:B] ?",
            [1, 2],
        )
    )
    print(
        filler.fill_count_query(
            "How many [person->image:NOUN:A:2] does the [person->person:NOUN:A:1] of the ["
            "literary_work->person:NOUN:A:0] of [literary_work:A] have ?",
            [3],
        )
    )

    print(filler.fill_single_ent_query("Who is [person:A] ?", [0]))
    print(filler.fill_multi_ent_query("Is [person:A] the [person->person:NOUN:B:0] of [person:B] ?", [0, 1]))


if __name__ == "__main__":
    typer.run(example)
