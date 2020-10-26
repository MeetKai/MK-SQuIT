# Copyright (c) 2020 MeetKai Inc. All rights reserved.

"""Preprocesses raw entity and property data from WikiData."""
import os
import re
import json
import random
from glob import glob
from typing import Dict
from itertools import groupby

import typer
import spacy
from tqdm import tqdm

nlp = spacy.load("en_core_web_sm")
merge_ents = nlp.create_pipe("merge_entities")
merge_nps = nlp.create_pipe("merge_noun_chunks")
nlp.add_pipe(merge_ents)
nlp.add_pipe(merge_nps)


def preprocess_things(data_dir: str = "./data", file_identifier: str = "*-5k.json"):
    """Preprocess things (essentially proper nouns) from WikiData with files named "*-5k.json":
        - Filters things
        - Combines thingLabel and thingAltLabel to labels field
    """
    fps = glob(os.path.join(data_dir, file_identifier))
    for fp in fps:
        print(f"Processing {fp}")
        # open and preprocess file
        preprocessed_data = []
        with open(fp, "r") as f:
            data = json.load(f)
            for thing in tqdm(data):
                # filter things
                if thing["thing"].split("/")[-1] != thing["thingLabel"]:
                    # clean label by removing parenthesis and everything inside
                    thing_label = thing.pop("thingLabel")
                    thing_label = re.sub(r"\([^)]*\)", "", thing_label).strip()

                    # combine thingLabel and thingAltLabel
                    label_set = set()
                    label_set.add(thing_label)
                    alt_labels = thing.pop("thingAltLabel", None)
                    if alt_labels:
                        alt_labels = re.sub(r"\([^)]*\)", "", alt_labels).strip()
                        for label in alt_labels.split(", "):
                            label_set.add(label)
                    thing["labels"] = sorted(label_set)

                    preprocessed_data.append(thing)

        # write to file
        base_fp, ext = os.path.splitext(fp)
        out_fp = base_fp + "-preprocessed" + ext
        with open(out_fp, "w") as f:
            json.dump(preprocessed_data, f, indent=4)
            print(f"Saved to {out_fp}\n")


def tag_prop(prop: Dict) -> Dict:
    """Helper function for preprocess_properties:
        - Assigns a POS (pair) tag to each property (EX: [NOUN-ADP])
        - Filters props that have ID within their labels
        - Covers edge case where a word could be a noun or a verb
    """
    pos_dict = dict()
    for label in prop["labels"]:
        # deal with edge case for noun/verbs: beginning -> noun, instead of verb
        temp_label = label
        if len(label.split(" ")) <= 1:
            temp_label = "the " + temp_label

        # get pos tokens using spacy and process them
        pos_tokens = [
            token.pos_ if token.pos_ != "PROPN" else "NOUN"
            for token in nlp(temp_label)
            if token.pos_ not in ["DET", "PUNCT"]
        ]

        # we only care about the first and last pos
        if len(pos_tokens) > 2:
            pos_tokens = [pos_tokens[0], pos_tokens[-1]]

        # remove consecutive duplicates: NOUN-NOUN -> NOUN
        pos_tokens = [group[0] for group in groupby(pos_tokens)]

        # concat into str
        pos = "-".join(pos_tokens)

        if pos_dict.get(pos) is None:
            pos_dict[pos] = []
        pos_dict[pos].append(label)
    prop["pos"] = pos_dict
    return prop


def preprocess_properties(data_dir: str = "./data", file_identifier: str = "*-props.json"):
    """Preprocesses properties from WikiData with files determined by the file_identifier:
        - Adds type field (must be manually annotated afterwards)
        - Combines propLabel and propAltLabel to labels field
        - Filters out properties that are IDs
        - Tag properties with POS-tags and sort by them
    """
    fps = glob(os.path.join(data_dir, file_identifier))
    for fp in fps:
        print(f"Processing {fp}")
        prefix = os.path.basename(fp).replace("-props.json", "")
        preprocessed_data = []
        with open(fp, "r") as f:
            data = json.load(f)
            for prop in tqdm(data):
                # add typing for graph traversal
                prop["type"] = prefix + "->"

                # clean label by removing parenthesis and everything inside
                prop_label = prop.pop("propLabel")
                prop_label = re.sub(r"\([^)]*\)", "", prop_label)

                # combine propLabel and propAltLabel
                label_set = set()
                label_set.add(prop_label.strip())
                alt_labels = prop.pop("propAltLabel", None)
                if alt_labels:
                    alt_labels = re.sub(r"\([^)]*\)", "", alt_labels)
                    for label in alt_labels.split(", "):
                        label_set.add(label.strip())
                prop["labels"] = sorted(label_set)

                # if a prop is an ID, ignore it
                is_id = False
                for label in prop["labels"]:
                    if label[-2:] == "ID":
                        is_id = True
                        break
                if not is_id:
                    preprocessed_data.append(prop)

            preprocessed_data = [tag_prop(prop) for prop in tqdm(preprocessed_data)]

        # write to file
        base_fp, ext = os.path.splitext(fp)
        out_fp = base_fp + "-preprocessed" + ext
        with open(out_fp, "w") as f:
            json.dump(preprocessed_data, f, indent=4)
            print(f"Saved to {out_fp}\n")


def generate_pos_examples(data_dir: str = "./data", num_samples: int = 10):
    """Aggregates all POS-tags and provides a few examples for each.
    Useful for manually labeling the typing system.
    """
    print(f"Generating type examples")
    fps = glob(os.path.join(data_dir, "*-props-preprocessed.json"))

    prop_list = []
    for fp in fps:
        with open(fp, "r") as f:
            data = json.load(f)
            prop_list = prop_list + data

    pos_dict = dict()
    for prop in tqdm(prop_list):
        for pos in prop["pos"].keys():
            if pos not in pos_dict.keys():
                pos_dict[pos] = set()
            pos_dict[pos].update(prop["pos"][pos])  # set

    # order by len
    sorted_keys = sorted(pos_dict, key=lambda k: len(pos_dict[k]), reverse=True)

    # write to file
    out_fp = os.path.join(data_dir, "pos-examples.txt")
    with open(out_fp, "w") as f:
        for key in sorted_keys:
            f.write(f"Key: [{key}] | Len: {len(pos_dict[key])}\n")
            items = random.sample(list(pos_dict[key]), min(len(pos_dict[key]), num_samples))
            for prop in items:
                f.write(f"\t{prop}\n")
            f.write(f"\n")
        print(f"Saved to {out_fp}")


def main(
    data_dir: str = "./data",
    ent_id: str = "*-5k.json",
    prop_id: str = "*-props.json",
    num_examples_to_generate: int = 10,
):
    """Preprocesses entity and property data for the generation pipeline.

    python -m scripts.preprocess \
    --data-dir ./data \
    --ent-id *-5k.json \
    --prop-id *-props.json \
    --num-examples-to-generate 10

    Args:
        data_dir: Data directory.
        ent_id: Glob identifier for entity data.
        prop_id: Glob identifier for property data.
        num_examples_to_generate: Number of examples to generate for each POS tag. If <= 0, pos-examples.txt is not generated.

    Outputs:
        *-5k-preprocessed.json: Preprocessed entity data.
        *-props-preprocessed.json: Preprocessed property data.
        pos-examples.txt: Part-of-speech samples sorted by occurrences.
    """
    preprocess_things(data_dir=data_dir, file_identifier=ent_id)
    preprocess_properties(data_dir=data_dir, file_identifier=prop_id)
    if num_examples_to_generate > 0:
        generate_pos_examples(data_dir=data_dir, num_samples=num_examples_to_generate)


if __name__ == "__main__":
    typer.run(main)
