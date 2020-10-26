# Copyright (c) 2020 MeetKai Inc. All rights reserved.

import os
import json
import random
from glob import glob
from typing import Dict, List

import typer


class PredicateBank(object):
    """Provides functions to randomly pull specifics for template filling:
        - Loads predicate dictionaries
        - Loads property dictionaries
        - Loads the autogenerated type list
    """

    def __init__(
        self,
        data_dir: str = "./data",
        property_file_identifier: str = "*-props-preprocessed.json",
        entity_file_identifier: str = "*-5k-preprocessed.json",
        type_list_file_name: str = "type-list-autogenerated.json",
    ):
        self.bank = self._load_predicate_bank(data_dir=data_dir, file_identifier=property_file_identifier)
        self.type_list = self._load_type_list(data_dir=data_dir, file_name=type_list_file_name)
        self.things = self._load_things(
            data_dir=data_dir, file_identifier=entity_file_identifier, thing_types=self.type_list["start_domains"]
        )

    def _load_predicate_bank(self, data_dir: str, file_identifier: str) -> Dict:
        fps = glob(os.path.join(data_dir, file_identifier))

        predicates = []
        for fp in fps:
            with open(fp, "r") as f:
                preds = json.load(f)
                predicates.extend(preds)

        predicate_bank = {}
        for pred in predicates:
            if pred["type"] in predicate_bank:
                predicate_bank[pred["type"]].append(pred)
            else:
                predicate_bank.update({pred["type"]: [pred]})

        return predicate_bank

    def _load_type_list(self, data_dir: str, file_name: str) -> Dict:
        fp = os.path.join(data_dir, file_name)
        with open(fp, "r") as f:
            type_list = json.load(f)
        return type_list

    def _load_things(self, data_dir: str, file_identifier: str, thing_types: List[str]) -> Dict:
        things = dict()
        for thing_name in thing_types:
            fp = os.path.join(data_dir, thing_name + file_identifier[1:])
            with open(fp, "r") as f:
                things[thing_name] = json.load(f)
        return things

    def get_thing(self, thing_type: str) -> str:
        """
        Args:
            thing_type: one of the major categories "television_series", "person", "movie", "literary_work"

        Returns:
            a random label associated with thing
        """
        return random.choice(random.choice(self.things[thing_type])["labels"])
        # return random.choice(random.choice(self.things["chemical"])["labels"])

    def get_predicate(self, predicate_type: str, part_of_speech: str, patience_limit: int = 50) -> (str, str):
        """
        Args:
            predicate_type: "person->location"
            part_of_speech: "NOUN", "VERB-ABP", "VERB"
            patience_limit: limit to how random predicates to look through

        Returns:
            predicate and its P-value with a given type and part of speech tag
        """
        part_of_speech = part_of_speech.upper()  # ensure all capitalized
        item = random.choice(self.bank[predicate_type])
        patience = 0
        while part_of_speech not in item["pos"].keys():
            if patience >= patience_limit:
                return None
            item = random.choice(self.bank[predicate_type])
            patience += 1
        return random.choice(item["pos"][part_of_speech]), item["prop"].split("/")[-1]

    def get_wh_word(self, thing_type: str) -> str:
        """
        Args:
            thing_type: any type category

        Returns:
            WH value in the autogenerated types list
        """
        return self.type_list["types"][thing_type]["WH"]


def example(data_dir: str = "data", prop_id: str = "*-props-preprocessed.json", ent_id: str = "*-5k-preprocessed.json"):
    """PredicateBank example functionality.

    python -m mk_squit.generation.predicate_bank \
        --data-dir data \
        --prop-id *-props-preprocessed.json \
        --ent-id *-5k-preprocessed.json
    """
    pb = PredicateBank(data_dir=data_dir, property_file_identifier=prop_id, entity_file_identifier=ent_id)

    print("Get a thing from a start domain category:")
    print(f"\t{pb.get_thing('television_series')}")
    print(f"\t{pb.get_thing('person')}")
    print(f"\t{pb.get_thing('movie')}")
    print(f"\t{pb.get_thing('literary_work')}")
    # print(f"\t{pb.get_thing('chemical')}\n")

    print("Get a predicate and p-value given the type and POS:")
    print(f"\t{pb.get_predicate('person->location', 'NOUN')}\n")

    print("Get a WH word (question identifier) given a specific type:")
    print(f"\t{pb.get_wh_word('height')}")


if __name__ == "__main__":
    typer.run(example)