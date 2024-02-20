from rag.agents.interface import Pipeline
from typing import Any
import warnings
import os
import box
import yaml
from rich import print
import ollama


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

        file_list = [os.path.join(cfg.DATA_PATH, f) for f in os.listdir(cfg.DATA_PATH)
                     if os.path.isfile(os.path.join(cfg.DATA_PATH, f)) and not f.startswith('.')
                     and not f.lower().endswith('.pdf')]

        print("Query: " + query + "\n")

        res = ollama.chat(
            model="llava:7b-v1.6-mistral-q5_K_M",
            messages=[
                {
                    'role': 'user',
                    'content': query,
                    'images': file_list
                }
            ]
        )

        print(res['message']['content'])
