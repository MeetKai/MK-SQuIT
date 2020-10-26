#!/bin/bash
# Copyright (c) 2020 MeetKai Inc. All rights reserved.

# Get latest version of NeMo.
pip install Cython
python -m pip install git+https://github.com/NVIDIA/NeMo.git@main#egg=nemo_toolkit[nlp]

# Download scripts.
mkdir conf
mkdir data
wget https://raw.githubusercontent.com/NVIDIA/NeMo/main/examples/nlp/text2sparql/text2sparql.py
wget https://raw.githubusercontent.com/NVIDIA/NeMo/main/examples/nlp/text2sparql/evaluate_text2sparql.py
wget -P ./data https://raw.githubusercontent.com/NVIDIA/NeMo/main/examples/nlp/text2sparql/data/import_datasets.py
wget -P ./conf https://raw.githubusercontent.com/NVIDIA/NeMo/main/examples/nlp/text2sparql/conf/text2sparql_config.yaml
wget -P .. https://raw.githubusercontent.com/NVIDIA/NeMo/main/tutorials/nlp/Neural_Machine_Translation-Text2Sparql.ipynb