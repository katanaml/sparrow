from rag.agents.interface import Pipeline
from typing import Any
import warnings
import os
import box
import yaml
from rich import print
from ollama import Client


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

        query = "retrieve values of invoice number, invoice date fields from given document. im interested in actual values, no need to provide any descriptions"
        print("Query: " + query + "\n")

        client = Client(host='http://127.0.0.1:11434')
        res = client.chat(
            model="llava:13b",
            messages=[
                {
                    'role': 'user',
                    'content': query,
                    'images': file_list
                }
            ]
        )

        print(res['message']['content'])
