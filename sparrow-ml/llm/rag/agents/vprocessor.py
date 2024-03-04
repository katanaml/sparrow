from rag.agents.interface import Pipeline
from rich.progress import Progress, SpinnerColumn, TextColumn
import warnings
import box
import yaml
import timeit
from rich import print
from typing import Any


warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)


# Import config vars
with open('config.yml', 'r', encoding='utf8') as ymlfile:
    cfg = box.Box(yaml.safe_load(ymlfile))


class VProcessorPipeline(Pipeline):
    def run_pipeline(self,
                     payload: str,
                     query_inputs: [str],
                     query_types: [str],
                     query: str,
                     debug: bool = False,
                     local: bool = True) -> Any:
        print(f"\nRunning pipeline with {payload}\n")

        start = timeit.default_timer()

        end = timeit.default_timer()

        print('=' * 50)

        print(f"Time to retrieve answer: {end - start}")