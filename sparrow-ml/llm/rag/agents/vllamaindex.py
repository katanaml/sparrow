from rag.agents.interface import Pipeline
from typing import Any
import warnings
import os
import box
import yaml
import timeit
from rich import print
from pathlib import Path
from llama_index.core import SimpleDirectoryReader
from PIL import Image
import matplotlib.pyplot as plt
from llama_index.multi_modal_llms.ollama import OllamaMultiModal


warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)


# Import config vars
with open('config.yml', 'r', encoding='utf8') as ymlfile:
    cfg = box.Box(yaml.safe_load(ymlfile))


class VLlamaIndexPipeline(Pipeline):
    def run_pipeline(self,
                     payload: str,
                     query_inputs: [str],
                     query_types: [str],
                     query: str,
                     debug: bool = False,
                     local: bool = True) -> Any:
        print(f"\nRunning pipeline with {payload}\n")

        start = timeit.default_timer()

        file_list = [os.path.join(cfg.DATA_PATH, f) for f in os.listdir(cfg.DATA_PATH)
                     if os.path.isfile(os.path.join(cfg.DATA_PATH, f)) and not f.startswith('.')
                     and not f.lower().endswith('.pdf')]

        print("Query: " + query + "\n")

        mm_model = OllamaMultiModal(model="llava:13b")

        # load as image documents
        image_documents = SimpleDirectoryReader(cfg.DATA_PATH + "temp/").load_data()


        end = timeit.default_timer()

        print(f"\nJSON response:\n")
        print("answer" + '\n')
        print('=' * 50)

        print(f"Time to retrieve answer: {end - start}\n")


