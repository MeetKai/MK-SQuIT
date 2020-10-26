#!/bin/bash
# Copyright (c) 2020 MeetKai Inc. All rights reserved.

# Set parameters for train / eval.
export SRC_DATA_DIR=./out
export TGT_DATA_DIR=./out
export LOG_PATH=./out/NeMo_logs
export MODEL_PATH="$LOG_PATH"/bart.nemo
export BATCH_SIZE=32