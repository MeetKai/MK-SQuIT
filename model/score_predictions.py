# Copyright (c) 2020 MeetKai Inc. All rights reserved.

"""Run evaluation metrics on baseline predictions."""
import sys
from pathlib import Path
from typing import List

import typer
import numpy as np
import pandas as pd
from tqdm import tqdm

sys.path.append(str(Path(__file__).absolute().parent.parent))
from mk_squit.utils.metrics import Metrics


def score(gts: List[str], preds: List[str]):
    """"""
    results = [Metrics.evaluate(pred, gt) for gt, pred in tqdm(zip(gts, preds))]
    bleu_score = np.average([result[0] for result in results])
    rouge_1_score = np.average([result[1] for result in results])
    rouge_2_score = np.average([result[2] for result in results])
    rouge_l_score = np.average([result[3] for result in results])
    rouge_w_score = np.average([result[4] for result in results])
    print(f"BLEU: {bleu_score} | ROUGE-1: {rouge_1_score} | ROUGE-2: {rouge_2_score}")
    print(f"ROUGE-L: {rouge_l_score} | ROUGE-W: {rouge_w_score}")


def postprocess(text: str) -> str:
    """Simple postprocessing to correct formatting which isn't generated up due to BART tokenization."""
    text = text.replace(" (", " ( ")
    text = text.replace(") ", " ) ")
    text = text.replace(" [", " [ ")
    text = text.replace("] ", " ] ")
    text = text.replace("/", " / ")
    return text


def main(filepath: Path):
    df = pd.read_csv(str(filepath), sep="\t")
    score(gts=df.label.tolist(), preds=[postprocess(p) for p in df.predictions])


if __name__ == "__main__":
    typer.run(main)
