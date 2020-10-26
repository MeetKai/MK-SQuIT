# Baseline Model

The baseline model uses [NVIDIA NeMo](https://github.com/NVIDIA/NeMo) to fine tune a [BART](https://arxiv.org/abs/1910.13461) model from [facebook/bart-base](https://huggingface.co/transformers/pretrained_models.html).

*Note: This baseline model is meant to showcase usage and is not optimized for accuracy.*

## Setup
Install the latest version of NeMo and download the example scripts for Text2Sparql.
```
./setup.sh
``` 

## Update Train / Eval Parameters (Optional)
By default, the model is trained and evaluated with a batch size of 32. Data is stored to `out`. To change these, update `params.sh` before proceeding.
```
./params.sh
```

## Download, Reformat Data, and Train
Download and reformat the data before training (NeMo's [NeuralMachineTranslationDataset](https://github.com/NVIDIA/NeMo/blob/main/nemo/collections/nlp/data/neural_machine_translation/neural_machine_translation_dataset.py) expects a specific format).
Training configurations can be edited by adjusting [./conf/text2sparql_config.yaml](https://github.com/NVIDIA/NeMo/blob/main/examples/nlp/text2sparql/conf/text2sparql_config.yaml) before running this script or by modifying the args.
```
./train.sh
```
    
## Generate Predictions and Scores for Easy and Hard Data
Generate predictions to ./NeMo_logs and score them.
For evaluation, we found tradition methods of BLEU and ROUGE to be fair indicators of the model's performance.
```
./evaluate.sh
```

We get the following scores after fine tuning BART for 2 epochs: 

| Dataset   | BLEU    | ROUGE-1 | ROUGE-2 | ROUGE-L | ROUGE-W |
|-----------|---------|---------|---------|---------|---------|
| test-easy | 0.98841 | 0.99581 | 0.99167 | 0.99581 | 0.71521 |
| test-hard | 0.59669 | 0.78746 | 0.73099 | 0.78164 | 0.48497 |

Finetuned BART performs well on the easy test set, but struggles with with the more complex logical requirements, noisy perturbations, and additional unseen slot domains in the hard set.

## Notebook
A tutorial for NeMo is also available [here](https://github.com/NVIDIA/NeMo/blob/main/tutorials/nlp/Neural_Machine_Translation-Text2Sparql.ipynb).