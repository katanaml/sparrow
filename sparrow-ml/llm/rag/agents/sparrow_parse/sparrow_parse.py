from rag.agents.interface import Pipeline
import timeit
import box
import yaml
from rich import print
from typing import Any, List
import warnings


warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)


class SparrowParsePipeline(Pipeline):
    def run_pipeline(self,
                     payload: str,
                     query_inputs: [str],
                     query_types: [str],
                     keywords: [str],
                     query: str,
                     file_path: str,
                     index_name: str,
                     options: List[str] = None,
                     group_by_rows: bool = True,
                     update_targets: bool = True,
                     debug: bool = False,
                     local: bool = True) -> Any:
        print(f"\nRunning pipeline with {payload}\n")

        # Import config vars
        with open('config.yml', 'r', encoding='utf8') as ymlfile:
            cfg = box.Box(yaml.safe_load(ymlfile))

        start = timeit.default_timer()

        answer = "OK"

        end = timeit.default_timer()

        print(f"\nJSON response:\n")
        print(answer)
        print('\n')
        print('=' * 50)

        print(f"Time to retrieve answer: {end - start}")

        return answer