from inference import inference_call
from training import training_call
from evaluate import evaluate_call
import json
import argparse
import os
import sys


def inference(api_url, file_path, model_in_use, sparrow_key):
    result = inference_call(api_url, file_path, model_in_use, sparrow_key)
    pretty_result = json.dumps(json.loads(result), indent=4)
    print(pretty_result)


def training(api_url, max_epochs, val_check_interval, warmup_steps, model_in_use, sparrow_key):
    result = training_call(api_url, max_epochs, val_check_interval, warmup_steps, model_in_use, sparrow_key)
    pretty_result = json.dumps(json.loads(result), indent=4)
    print(pretty_result)


def evaluate(api_url, model_in_use, sparrow_key):
    result = evaluate_call(api_url, model_in_use, sparrow_key)
    pretty_result = json.dumps(json.loads(result), indent=4)
    print(pretty_result)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Sparrow CLI')
    parser.add_argument('-a', '--api_url', type=str, required=True, help='API URL')
    parser.add_argument('-t', '--type', type=str, required=True, help='Inference or Training')
    parser.add_argument('-f', '--file_path', type=str, help='File path')
    parser.add_argument('-me', '--max_epochs', type=int, help='Max Epochs')
    parser.add_argument('-vci', '--val_check_interval', type=float, help='Validation Check Interval')
    parser.add_argument('-ws', '--warmup_steps', type=int, help='Warmup Steps')
    parser.add_argument('-m', '--model_in_use', type=str, help='Model in use')
    parser.add_argument('-k', '--sparrow_key', type=str, required=True, help='Sparrow key')

    args = parser.parse_args()

    api_url = args.api_url
    sparrow_key = args.sparrow_key
    file_path = args.file_path
    model_in_use = args.model_in_use
    max_epochs = args.max_epochs
    val_check_interval = args.val_check_interval
    warmup_steps = args.warmup_steps

    if args.type == 'inference':
        if not os.path.exists(file_path):
            print("File does not exist")
            sys.exit(1)

        inference(api_url, file_path, model_in_use, sparrow_key)
    elif args.type == 'training':
        training(api_url, max_epochs, val_check_interval, warmup_steps, model_in_use, sparrow_key)
    elif args.type == 'evaluate':
        evaluate(api_url, model_in_use, sparrow_key)
