# Copyright (c) 2020 MeetKai Inc. All rights reserved.

import os
import re
import json
from typing import Dict, Tuple

from rapidfuzz import fuzz, process
from glob import glob


def url_to_qvalue(url: str) -> str:
    """Get q value from Wikidata url.
    http://www.wikidata.org/entity/Q494 -> Q494
    """
    return url.split("/")[-1]


def load_entities(data_dir: str) -> Dict:
    """Load entity data."""
    assert os.path.isdir(data_dir), f"{data_dir} is not a valid directory."
    fps = glob(os.path.join(data_dir, "*-5k-preprocessed.json"))
    data = []
    for fp in fps:
        with open(fp, "r") as f:
            file_data = json.load(f)
            data.extend(file_data)
    assert data, f"No data was found, please check {data_dir}."

    # expand data
    expanded_data = dict()
    for item in data:
        qvalue = url_to_qvalue(item["thing"])
        for label in item["labels"]:
            expanded_data[label] = qvalue

    return expanded_data


class EntityResolver:
    """Uses fuzzy text matching to map [entity-name] to its Q-value."""

    def __init__(self, data_dir: str, score_cutoff: float = 80.0):
        self.entity_dict = load_entities(data_dir)
        self.choices = list(self.entity_dict.keys())
        self.score_cutoff = score_cutoff

    def resolve_entity(self, entity: str) -> Tuple[str, str, float]:
        """Finds the fuzzy entity match above the cutoff score and returns the Q-value for it.

        Returns:
            (q-value, top_entity_match, simple_levenshtein_score)
        """
        top = process.extractOne(entity, self.choices, scorer=fuzz.ratio, score_cutoff=self.score_cutoff)
        if not top:
            raise ValueError(f"For entity [{entity}], no valid match above cutoff found.")
        return self.lookup(top[0]), top[0], top[1]

    def lookup(self, entity: str):
        return self.entity_dict[entity]

    def resolve(self, text: str) -> str:
        """Replaces all entity matches within a predicted query
        assuming entities are always formatted between two brackets.
        """
        matches = re.findall(r"\[(.*?)\]", text)
        for entity in matches:
            try:
                q_value = self.resolve_entity(entity)[0]
                text = text.replace(f"[{entity}]", f"wd:{q_value}")
            except ValueError as e:
                print(f"WARNING: {e}")
        return text
