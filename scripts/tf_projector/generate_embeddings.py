# Copyright (c) 2020 MeetKai Inc. All rights reserved.

"""Generates USE-4 embeddings for visualization in tensorflow projector."""
import io
import os

import typer
import pandas as pd
from tqdm import tqdm
import tensorflow_hub as hub


def query_type(query: str) -> str:
    if "COUNT" in query:
        return "count"
    if "ASK" in query:
        return "boolean"  # change to another color
    return "fact"


def main(data_dir: str = "out/tf_projector", data_path: str = "out/train_queries_v3.tsv"):
    """Generates embeddings for tf_projector. Requires a significant amount of space to store vectors.
    
    Args:
        data_dir: Directory to save tf projector metadata.
        data_path: Path to data to visualize.
    """
    os.makedirs(data_dir, exist_ok=True)

    train_df = pd.read_csv(data_path, delimiter="\t")

    embed = hub.load("https://tfhub.dev/google/universal-sentence-encoder/4")
    print("Embedding...")
    emb_utters = embed(train_df.english.tolist()).numpy()

    vecs_path = os.path.join(data_dir, "vecs.tsv")
    meta_path = os.path.join(data_dir, "meta.tsv")
    out_v = io.open(vecs_path, "w", encoding="utf-8")
    out_m = io.open(meta_path, "w", encoding="utf-8")

    out_m.write("utter\tsparql\tquestion_type\n")
    for utter, sparql, embedding in tqdm(zip(train_df.english, train_df.sparql, emb_utters)):
        out_m.write(utter + "\t" + sparql + "\t" + query_type(sparql) + "\n")
        out_v.write("\t".join([str(x) for x in embedding]) + "\n")
    out_m.close()
    out_v.close()


if __name__ == "__main__":
    typer.run(main)
