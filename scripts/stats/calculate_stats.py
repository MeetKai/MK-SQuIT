# Copyright (c) 2020 MeetKai Inc. All rights reserved.

"""Calculate stats related to dataset as well as some related to the BART model."""
import os
import sys
import json
from pathlib import Path
from glob import glob

import typer
import numpy as np

sys.path.append(str(Path(__file__).absolute().parent.parent.parent))
from mk_squit.generation.template_generator import TemplateGenerator
from mk_squit.generation.type_generator import TypeGenerator


def main(data_dir: str = "./data", verbose: bool = False):
    """Calculate stats.

    Args:
        data_dir: Data directory containing generation source files.
        verbose: Print verbose.
    """
    file_identifier = "*-props-preprocessed.json"
    fps = glob(os.path.join(data_dir, file_identifier))

    entities = []
    for fp in fps:
        with open(fp, "r") as f:
            preds = json.load(f)
            entities.extend(preds)

    # number of p-values
    predicate_bank = {}
    for ent in entities:
        p_value = ent["prop"].split("/")[-1]
        if p_value in predicate_bank:
            predicate_bank[p_value].append(ent)
        else:
            predicate_bank.update({p_value: [ent]})

    print(f"# of p-values (properties): {len(predicate_bank)}")
    if verbose:
        print(predicate_bank.keys())

    label_set = set()
    num_labels = []
    predicate_types = dict()
    pos_label_dict = dict()
    subject_dict = dict()
    for p_value in predicate_bank.keys():
        for predicate in predicate_bank[p_value]:
            for label in predicate["labels"]:
                label_set.add(label)

            num_labels.append(len(predicate["labels"]))

            if predicate["type"] in predicate_types:
                predicate_types[predicate["type"]].append(p_value)
            else:
                predicate_types.update({predicate["type"]: [p_value]})

            pos_labels = predicate["pos"].keys()
            for label in pos_labels:
                if label in pos_label_dict:
                    pos_label_dict[label].append(p_value)
                else:
                    pos_label_dict.update({label: [p_value]})

            subject = predicate["type"].split("->")[0]
            if subject in subject_dict:
                subject_dict[subject].append(p_value)
            else:
                subject_dict.update({subject: [p_value]})

    # number of unique labels
    print(f"# of predicate labels: {len(label_set)}")
    if verbose:
        print(label_set)

    # breakdown of predicates by type
    print("breakdown of predicates by type:")
    for pair in sorted(predicate_types.items(), key=lambda x: len(x[1]), reverse=True):
        predicate_type = pair[0]
        print(f"\t{predicate_type}: {len(predicate_types[predicate_type])}")
        if verbose:
            print(predicate_types)

    # breakdown of predicates by what POS labels they have
    print("breakdown of predicates by pos labels:")
    for pair in sorted(pos_label_dict.items(), key=lambda x: len(x[1]), reverse=True):
        pos_type = pair[0]
        print(f"\t{pos_type}: {len(pos_label_dict[pos_type])}")
        if verbose:
            print(pos_label_dict[pos_type])

    # average number of labels per predicate (including primary label)
    print(f"avg # of labels per predicate: {np.average(num_labels)}")

    # number of predicates by subject domain
    print("# of predicates by subject:")
    for subject in subject_dict:
        print(f"\t{subject}: {len(subject_dict[subject])}")

    #######################################################################
    #######################################################################
    #######################################################################

    file_identifier: str = "*-5k-preprocessed.json"
    fps = glob(os.path.join(data_dir, file_identifier))

    entities = []
    for fp in fps:
        with open(fp, "r") as f:
            data = json.load(f)
            entities.extend(data)

    # number of individual entities
    entity_bank = {}
    for ent in entities:
        q_value = ent["thing"].split("/")[-1]
        if q_value in entity_bank:
            entity_bank[q_value].append(ent)
        else:
            entity_bank.update({q_value: [ent]})

    # number of individual entities
    print(f"# of q-values (entities): {len(entity_bank)}")
    if verbose:
        print(entity_bank.keys())

    # number of labels per q-value and aliases
    label_set = set()
    num_labels = []
    for q_value in entity_bank.keys():
        for ent in entity_bank[q_value]:
            for label in ent["labels"]:
                label_set.add(label)
            num_labels.append(len(ent["labels"]))
    print(f"# of entitiy labels: {len(label_set)}")
    if verbose:
        print(label_set)

    # average number of labels per entity (including primary label)
    print(f"avg # of labels per entity: {np.average(num_labels)}")

    #######################################################################
    #######################################################################
    #######################################################################

    temp_gen = TemplateGenerator()
    # num of baseline templates
    num_baseline_templates = 0
    for template_type in temp_gen.base_templates.keys():
        num_baseline_templates += len(temp_gen.base_templates[template_type])
    print(f"# of baseline templates: {num_baseline_templates}")

    # num of typed templates
    type_gen = TypeGenerator()
    thing_types = ["movie", "person", "literary_work", "television_series"]
    total_num_paths = 0
    total_num_possible_queries = 0
    for template_type in temp_gen.templates.keys():
        for num_template_tuple in temp_gen.templates[template_type]:
            num_template = num_template_tuple[0]
            pred_chain_lengths = num_template_tuple[1]
            if len(pred_chain_lengths) == 1:
                for thing in thing_types:
                    paths = list(
                        type_gen.generate_unidirectional_pred_traversal(
                            type_gen.G, thing.lower(), pred_chain_lengths[0]
                        )
                    )
                    total_num_paths += len(paths)
                    if verbose:
                        print(f"Unidirectional - {thing} - {pred_chain_lengths} - paths: {len(paths)}")
            else:
                for thing_1 in thing_types:
                    for thing_2 in thing_types:
                        paths = type_gen.generate_bidirectional_pred_traversal(
                            thing_1.lower(),
                            thing_2.lower(),
                            *pred_chain_lengths,
                            type_gen.G,
                            type_gen.Gi,
                            debug_stats=True,
                        )
                        total_num_paths += len(paths)
                        if verbose:
                            print(f"Bidirectional - {thing_1} - {thing_2} - {pred_chain_lengths} - {len(paths)} paths")
    print(f"# of typed templates: {total_num_paths}")


if __name__ == "__main__":
    typer.run(main)
