# Copyright (c) 2020 MeetKai Inc. All rights reserved.

import re
import json
import random
from typing import List

import typer
from nltk import grammar as nltk_grammar
from nltk import CFG
from nltk.parse.generate import generate

from mk_squit.generation.type_generator import TypeGenerator
from mk_squit.generation.predicate_bank import PredicateBank

# Multi-fact questions bring forth referent ambiguities:
#    "What is the name of the sister city tied to Kansas City,
#    which is located in the county of Seville Province?"
# Which city does "which" refer to?

#### These grammars are for the TEST_HARD set
# single_ent_template_grammar = CFG.fromstring(
#     """
# S -> "[WH]" IS Q "?" | CAN "[WH]" IS Q "?"
# CAN -> "Hey" | "Can you tell me" | "Do you know"
# IS -> "is" | "was"
# Q -> NOUN | VERB-ADP
# NOUN -> "[THING]" | NOUN "'s [NOUN]" | "the [NOUN] of" NOUN
# VERB-ADP -> NOUN "[VERB-ADP]"
# """
# )
#
# multi_ent_template_grammar = CFG.fromstring(
#     """
# S -> IS NOUN "[SEP] the [NOUN] of" NOUN "?" | CAN is NOUN "[SEP] the [NOUN] of" NOUN "?"
# CAN -> "Hey" | "Can you tell me" | "Do you know"
# is -> "is" | "was"
# IS -> "Is" | "Was"
# NOUN -> "[THING]" | NOUN "'s [NOUN]" | "the [NOUN] of" NOUN
# """
# )
#
# count_template_grammar = CFG.fromstring(
#     """
# S -> "[WH]" IS Q "?" | "How many [NOUN] does" NOUN "have ?" | CAN "[WH]" IS Q "?" | CAN "how many [NOUN] does" NOUN "have ?"
# CAN -> "Hey" | "Can you tell me" | "Do you know"
# IS -> "is" | "was"
# Q -> "the number of [NOUN] of" NOUN
# NOUN -> "[THING]" | NOUN "'s [NOUN]" | "the [NOUN] of" NOUN
# """
# )

single_ent_template_grammar = CFG.fromstring(
    """
S -> "[WH]" IS Q "?"
IS -> "is" | "was"
Q -> NOUN | VERB-ADP
NOUN -> "[THING]" | NOUN "'s [NOUN]" | "the [NOUN] of" NOUN
VERB-ADP -> NOUN "[VERB-ADP]"
"""
)

multi_ent_template_grammar = CFG.fromstring(
    """
S -> IS NOUN "[SEP] the [NOUN] of" NOUN "?"
is -> "is" | "was"
IS -> "Is" | "Was"
NOUN -> "[THING]" | NOUN "'s [NOUN]" | "the [NOUN] of" NOUN
"""
)

count_template_grammar = CFG.fromstring(
    """
S -> "[WH]" IS Q "?" | "How many [NOUN] does" NOUN "have ?"
CAN -> "Hey" | "Can you tell me" | "Do you know"
IS -> "is" | "was"
Q -> "the number of [NOUN] of" NOUN
NOUN -> "[THING]" | NOUN "'s [NOUN]" | "the [NOUN] of" NOUN
"""
)


class TemplateGenerator(object):
    """Generates multiple layers of templates using a TypeGenerator and PredicateBank."""

    def __init__(self, type_generator: TypeGenerator, predicate_bank: PredicateBank):
        self.base_templates = {
            "single_entity": self.generate_base_templates(single_ent_template_grammar, depth=6),
            "multi_entity": self.generate_base_templates(multi_ent_template_grammar, depth=4),
            "count": self.generate_base_templates(count_template_grammar, depth=5),
            # "single_entity": self.generate_base_templates(single_ent_template_grammar, depth=8),  # TEST_HARD
            # "multi_entity": self.generate_base_templates(multi_ent_template_grammar, depth=6),
            # "count": self.generate_base_templates(count_template_grammar, depth=7),
        }
        self.templates = {
            "single_entity": [self.number_single_ent(template) for template in self.base_templates["single_entity"]],
            "multi_entity": [self.number_multi_ent(template) for template in self.base_templates["multi_entity"]],
            "count": [self.number_count_ent(template) for template in self.base_templates["count"]],
        }
        self.type_gen = type_generator
        self.predicate_bank = predicate_bank

    def generate_base_templates(self, grammar: nltk_grammar, depth: int) -> List[str]:
        templates = []
        for sentence in generate(grammar, depth=depth):
            templates.append(" ".join(sentence))
        return templates

    def save_base_templates(self, path: str = "./data/base_templates.json") -> None:
        with open(path, "w") as f:
            json.dump(self.base_templates, f)

    def __str__(self):
        return json.dumps(self.base_templates, indent=4)

    def number_single_ent(self, text_template: str, suffix: str = "A") -> (str, int):
        """
        Args:
            text_template: "[WH] is the [NOUN] of [THING] [VERB-ADP] ?"
            suffix: "A", "B"

        Returns:
            number template and the length of the predicate chain(s)
            "[WH] is the [NOUN:A:0] of [THING:A] [VERB-ADP:A:1] ?", [2]

        Numbering the template at this stage allows for greater ease when generating the corresponding SPARQL query
        The order of the predicates in the SPARQL query match the numbering of the predicates in the number template
        i.e. "[WH] is the [NOUN:A:0] of [THING:A] [VERB-ADP:A:1] ?
        -->  ?[THING:A] wdt:[NOUN:A:0]/wdt:[VERB-ADP:A:1] ?end .

        The [NOUN]s are numbered in the following manner:
            firstly in ascending order starting from 0 AFTER the [THING] token
            secondly in descending order BEFORE the [THING] token
        Then the [VERB-ADP]s are numbered in ascending order starting after the [THING] token
        """
        text_template = text_template.replace("[THING]", f"[THING:{suffix}]")
        thing_ind = text_template.find(f"[THING:{suffix}]")
        new_template = ""
        counter = 0

        for i in range(thing_ind, len(text_template)):
            new_template += text_template[i]
            if new_template[-5:] == "[NOUN":
                new_template += f":{suffix}:{counter}"
                counter += 1
        for i in range(thing_ind - 1, -1, -1):
            if new_template[:6] == "[NOUN]":
                new_template = new_template[:5] + f":{suffix}:{counter}]" + new_template[6:]
                counter += 1
            new_template = text_template[i] + new_template

        if new_template.find("[VERB-ADP]") != -1:
            new_template = new_template.replace("[VERB-ADP]", f"[VERB-ADP:{suffix}:{counter}]")
            counter += 1
        return new_template, [counter]

    def number_multi_ent(self, text_template: str) -> (str, int, int):
        """
        Args:
            text_template: "Is [THING] 's [NOUN] [SEP] the [NOUN] of the [NOUN] of [THING] ?"

        Returns:
            number template and the length of the predicate chain(s)
            "Is [THING:A] 's [NOUN:A:0] the [NOUN:B:1] of the [NOUN:B:0] of [THING:B] ?", [1, 2]

        The text_template is split on a [SEP] token, passed into number_single_ent, and then rejoined without [SEP]
        """
        sep_ind = text_template.find("[SEP]")
        templateA, countA = self.number_single_ent(text_template[:sep_ind], "A")
        templateB, countB = self.number_single_ent(text_template[sep_ind + 6 :], "B")

        return templateA + templateB, [countA[0], countB[0]]

    def number_count_ent(self, text_template: str) -> (str, int):
        """
        Args:
            text_template: "How many [NOUN] does [THING] 's [NOUN] 's [NOUN] have ?"

        Returns:
            number template and the length of the predicate chain(s)
            "How many [NOUN:A:2] does [THING:A] 's [NOUN:A:0] 's [NOUN:A:1] have ?", [3]

        The text_template is split on a [SEP] token, passed into number_single_ent, and then rejoined without [SEP]
        """
        return self.number_single_ent(text_template=text_template)

    def type_template(self, number_template: str, pred_chain_lengths: List[int]) -> (str, List[int]):
        """
        Args:
            number_template: "[WH] is the [NOUN:A:1] of the [NOUN:A:0] of [THING:A] ?"
            pred_chain_lengths: [2]

        Returns:
            type template and the length of the predicate chain(s)
            "What is the [literary_work->award:NOUN:A:1] of the
             [literary_work->literary_work:NOUN:A:0] of [literary_work:A] ?", [2]
        """
        suffixes = ["A", "B"]
        thing_types = ["movie", "person", "literary_work", "television_series"]

        paths = None
        thing_samples = None
        tries = 10

        # This for loop ensures that a pred chain is found eventually
        for i in range(tries):
            # for each thing, sample a start domain type
            thing_samples = random.choices(thing_types, k=len(pred_chain_lengths))
            if len(thing_samples) == 1:
                p = list(
                    self.type_gen.generate_unidirectional_pred_traversal(
                        self.type_gen.G, thing_samples[0].lower(), pred_chain_lengths[0]
                    )
                )
                if len(p) == 0:
                    return None
                paths_chosen = random.choice(p)
                paths = [paths_chosen[0]]
                number_template = number_template.replace("[WH]", self.predicate_bank.get_wh_word(paths_chosen[1])[0])
            else:
                paths = self.type_gen.generate_bidirectional_pred_traversal(
                    thing_samples[0].lower(),
                    thing_samples[1].lower(),
                    *pred_chain_lengths,
                    self.type_gen.G,
                    self.type_gen.Gi,
                )
            if paths or i == tries - 1:
                break
        # A path might not exist
        if paths is None:
            return None

        pred_pattern = r"\[\w+-?\w+:"  # Matches [NOUN:
        for i in range(len(thing_samples)):
            number_template = number_template.replace(f"[THING:{suffixes[i]}]", f"[{thing_samples[i]}:{suffixes[i]}]")
            path = paths[i]
            for j in range(pred_chain_lengths[i]):
                match = re.search(f"{pred_pattern}{suffixes[i]}:{j}]", number_template)
                number_template = number_template.replace(match.group(), "[" + path[j] + ":" + match.group()[1:])
        return number_template, pred_chain_lengths


def example(data_dir: str = "data", prop_id: str = "*-props-preprocessed.json", ent_id: str = "*-5k-preprocessed.json"):
    """TemplateGenerator example functionality.

    python -m mk_squit.generation.template_generator \
        --data-dir data \
        --prop-id *-props-preprocessed.json \
        --ent-id *-5k-preprocessed.json
    """
    pb = PredicateBank(data_dir=data_dir, property_file_identifier=prop_id, entity_file_identifier=ent_id)
    tg = TypeGenerator(pb)
    gen = TemplateGenerator(type_generator=tg, predicate_bank=pb)

    print("Base Templates:")
    print("\t", gen.base_templates["single_entity"][-1])
    print("\t", gen.base_templates["multi_entity"][-1])
    print("\t", gen.base_templates["count"][-1])
    # print("\t", sum([len(i) for i in gen.base_templates.values()]))
    print()

    print("Numbered Templates:")
    templates = gen.templates
    print("\t", templates["single_entity"][-1])
    print("\t", templates["multi_entity"][-1])
    print("\t", templates["count"][-1])
    print()

    print("Typed Templates:")
    print("\t", gen.type_template(*templates["single_entity"][-1]))
    print("\t", gen.type_template(*templates["multi_entity"][-1]))
    print("\t", gen.type_template(*templates["count"][-1]))


if __name__ == "__main__":
    typer.run(example)
