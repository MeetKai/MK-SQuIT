#!/bin/bash
# Copyright (c) 2020 MeetKai Inc. All rights reserved.

# Ensure params are set: ./params.sh
source ./params.sh

# Download and reformat data.
python ./data/import_datasets.py \
    --source_data_dir $SRC_DATA_DIR \
    --target_data_dir $TGT_DATA_DIR

# Train BART. Hyper-parameters can be updated as args shown below or directly within the config file (./conf/text2sparql_config.yaml).
python text2sparql.py \
    model.train_ds.filepath="$TGT_DATA_DIR"/train.tsv \
    model.validation_ds.filepath="$TGT_DATA_DIR"/test_easy.tsv \
    model.test_ds.filepath="$TGT_DATA_DIR"/test_hard.tsv \
    model.batch_size=$BATCH_SIZE \
    model.nemo_path=$MODEL_PATH \
    exp_manager.exp_dir=$LOG_PATH