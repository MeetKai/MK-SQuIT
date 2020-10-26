#!/bin/bash
# Copyright (c) 2020 MeetKai Inc. All rights reserved.

# Ensure params are set: ./params.sh
source ./params.sh

# Evaluate on test_easy.
python evaluate_text2sparql.py \
    model.test_ds.filepath="$TGT_DATA_DIR"/test_easy.tsv \
    model.batch_size=$BATCH_SIZE \
    model.nemo_path=$MODEL_PATH \
    exp_manager.exp_dir=$LOG_PATH

# Evaluate on test_hard.
python evaluate_text2sparql.py \
    model.test_ds.filepath="$TGT_DATA_DIR"/test_hard.tsv \
    model.batch_size=$BATCH_SIZE \
    model.nemo_path=$MODEL_PATH \
    exp_manager.exp_dir=$LOG_PATH

# Score
printf "Test easy:\n"
python -W ignore score_predictions.py "$LOG_PATH"/test_easy.tsv

printf "\nTest hard:\n"
python -W ignore score_predictions.py "$LOG_PATH"/test_hard.tsv