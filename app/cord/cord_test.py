from datasets import load_dataset
import datasets

datasets.logging.set_verbosity_info()
dataset = load_dataset('/Users/andrejb/infra/shared/katana-git/sparrow/app/cord/cord.py')