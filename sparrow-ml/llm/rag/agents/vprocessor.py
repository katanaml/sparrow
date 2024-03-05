from rag.agents.interface import Pipeline
from llama_index.core.program import LLMTextCompletionProgram
import json
from llama_index.llms.ollama import Ollama
from pydantic import BaseModel
from typing import List
from rich.progress import Progress, SpinnerColumn, TextColumn
import requests
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
                     file_path: str = None,
                     debug: bool = False,
                     local: bool = True) -> Any:
        print(f"\nRunning pipeline with {payload}\n")

        start = timeit.default_timer()

        if file_path is None:
            msg = "Please provide a file to process."
            print(msg)
            return msg

        with open(file_path, "rb") as file:
            files = {'file': (file_path, file, 'image/jpeg')}

            data = {
                'file': ''
            }

            response = self.invoke_pipeline_step(lambda: requests.post(cfg.VPROCESSOR_OCR_ENDPOINT,
                                                                       data=data,
                                                                       files=files,
                                                                       timeout=180),
                                                 "Running OCR...",
                                                 local)

            if response.status_code != 200:
                print('Request failed with status code:', response.status_code)
                print('Response:', response.text)

                return "Failed to process file. Please try again."

        data = response.json()

        class Receipt(BaseModel):
            guest_no: int
            cashier_name: str
            transaction_number: str
            receipt_items: List[str]
            total_amount_due: str
            receipt_date: str

        prompt_template_str = """\
        retrieve guest_no, cashier_name, transaction_number, names_of_receipt_items, total_amount_due, receipt_date. \
        using this structured data, coming from OCR {receipt_data}.\
        """

        llm_ollama = self.invoke_pipeline_step(lambda: Ollama(model=cfg.LLM_VPROCESSOR,
                                                              base_url=cfg.OLLAMA_BASE_URL_VPROCESSOR,
                                                              temperature=0,
                                                              request_timeout=900),
                                               "Loading Ollama...",
                                               local)

        program = LLMTextCompletionProgram.from_defaults(
            output_cls=Receipt,
            prompt_template_str=prompt_template_str,
            llm=llm_ollama,
            verbose=True,
        )

        output = self.invoke_pipeline_step(lambda: program(receipt_data=data),
                                           "Running inference...",
                                           local)

        answer = self.beautify_json(output.model_dump_json())

        end = timeit.default_timer()

        print(f"\nJSON response:\n")
        print(answer + '\n')
        print('=' * 50)

        print(f"Time to retrieve answer: {end - start}")

        return answer


    def invoke_pipeline_step(self, task_call, task_description, local):
        if local:
            with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    transient=False,
            ) as progress:
                progress.add_task(description=task_description, total=None)
                ret = task_call()
        else:
            print(task_description)
            ret = task_call()

        return ret


    def beautify_json(self, result):
        try:
            # Convert and pretty print
            data = json.loads(str(result))
            data = json.dumps(data, indent=4)
            return data
        except (json.decoder.JSONDecodeError, TypeError):
            print("The response is not in JSON format:\n")
            print(result)

        return {}