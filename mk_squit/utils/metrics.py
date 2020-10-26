# Copyright (c) 2020 MeetKai Inc. All rights reserved.

import re
from typing import List

import numpy as np

from nltk.translate.bleu_score import sentence_bleu
from rouge.rouge import rouge_n_sentence_level, rouge_l_sentence_level, rouge_w_sentence_level


class Metrics:
    """Calculates scores given a list of predictions and ground truths."""

    @staticmethod
    def tokenize_clauses(clause: str) -> List[str]:
        """
        Args:
            clause: "{ [ Aleksandr Kanaki ] ?end [ Adriaan Paulen ] wdt:P22 / wdt:P166 ?end . }"

        Returns: ['{', '[', 'Aleksandr Kanaki', ']', '?end', '[', 'Adriaan Paulen', ']', 'wdt:P22', '/', 'wdt:P166',
        '?end', '.', '}']

        Tokenizes but leaves entities as a single token for the purposes of BLEU. To tokenize normally, simply call
        clause.split(" ")
        """
        thing_matches = re.finditer(r"\[[^\]]+\]", clause)
        tokens = []
        i = 0
        for thing in thing_matches:
            tokens.extend(clause[i : thing.span()[0] - 1].split(" "))
            tokens.extend(["[", thing.group()[2:-2], "]"])
            i = thing.span()[1] + 1
        tokens.extend(clause[i:].split(" "))
        return tokens

    @staticmethod
    def evaluate(prediction: str, ground_truth: str) -> np.array:
        """
        Args:
            prediction:    "ASK { [ Aleksandr Kanaki ] ?end [ Adriaan Paulen ] wdt:P22 / wdt:P166 ?end . }"
            ground_truth:  "ASK { [ Aleksandr Kanaki ] wdt:P166 ?end . [ Adriaan Paulen ] wdt:P22 / wdt:P166 ?end . }"

        Returns:
            [0.74756512 0.94444444 0.82352941 0.94444444 0.57893533]
            [BLEU       ROUGE-1    ROUGE-2    ROUGE-L    ROUGE-W   ]

        The BLEU/ROUGE score evaluated on the entire query
        """
        gt_tokens = ground_truth.split(" ")
        pre_tokens = prediction.split(" ")

        results = np.zeros(5)

        # BLEU
        results[0] = sentence_bleu([gt_tokens], pre_tokens)

        # ROUGE-1
        results[1] = rouge_n_sentence_level(pre_tokens, gt_tokens, 1).f1_measure

        # ROUGE-2
        _, _, rouge_2 = rouge_n_sentence_level(pre_tokens, gt_tokens, 2)
        results[2] = rouge_2

        # ROUGE-L
        _, _, rouge_l = rouge_l_sentence_level(pre_tokens, gt_tokens)
        results[3] = rouge_l

        # ROUGE-W
        _, _, rouge_w = rouge_w_sentence_level(pre_tokens, gt_tokens)
        results[4] = rouge_w

        return results

    @staticmethod
    def weighted_evaluate(prediction: str, ground_truth: str) -> np.array:
        """
        Args:
            prediction:    "ASK { [ Aleksandr Kanaki ] ?end [ Adriaan Paulen ] wdt:P22 / wdt:P166 ?end . }"
            ground_truth:  "ASK { [ Aleksandr Kanaki ] wdt:P166 ?end . [ Adriaan Paulen ] wdt:P22 / wdt:P166 ?end . }"

        Returns:
            [0.69105389 0.93333333 0.78571429 0.93333333 0.58593202]
            [BLEU       ROUGE-1    ROUGE-2    ROUGE-L    ROUGE-W   ]

        Weighted average of the BLEU/ROUGE score evaluated on the clauses of the query and whether the surrounding query
        structure matches
        """
        pre_match = re.search(r"{.+}", prediction)
        gt_match = re.search(r"{.+}", ground_truth)

        if pre_match is None or gt_match is None:
            return np.zeroes(5)

        prediction_structure = prediction[: pre_match.span()[0]]
        ground_truth_structure = ground_truth[: gt_match.span()[0]]

        structure_score = int(prediction_structure == ground_truth_structure)

        prediction_clauses = pre_match.group()
        ground_truth_clauses = gt_match.group()

        gt_tokens = Metrics.tokenize_clauses(ground_truth_clauses)
        pre_tokens = Metrics.tokenize_clauses(prediction_clauses)

        # gt_tokens = ground_truth_clauses.split(" ")
        # pre_tokens = prediction_clauses.split(" ")

        results = np.zeros(5)

        # BLEU
        results[0] = sentence_bleu([gt_tokens], pre_tokens)

        # ROUGE-1
        results[1] = rouge_n_sentence_level(pre_tokens, gt_tokens, 1).f1_measure

        # ROUGE-2
        _, _, rouge_2 = rouge_n_sentence_level(pre_tokens, gt_tokens, 2)
        results[2] = rouge_2

        # ROUGE-L
        _, _, rouge_l = rouge_l_sentence_level(pre_tokens, gt_tokens)
        results[3] = rouge_l

        # ROUGE-W
        _, _, rouge_w = rouge_w_sentence_level(pre_tokens, gt_tokens)
        results[4] = rouge_w

        results *= 0.8 + structure_score * 0.2

        return results


def example():
    """Simple evaluation example."""
    print(
        Metrics.evaluate(
            "ASK { [ Aleksandr Kanaki ] ?end [ Adriaan Paulen ] wdt:P22 / wdt:P166 ?end . }",
            "ASK { [ Aleksandr Kanaki ] wdt:P166 ?end . [ Adriaan Paulen ] wdt:P22 / wdt:P166 ?end . }",
        )
    )


if __name__ == "__main__":
    example()
