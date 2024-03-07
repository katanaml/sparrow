from rag.agents.interface import Pipeline
from llama_index.core.program import LLMTextCompletionProgram
import json
from llama_index.llms.ollama import Ollama
from fastapi import UploadFile
from typing import List
from pydantic import create_model
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
                     file: UploadFile = None,
                     debug: bool = False,
                     local: bool = True) -> Any:
        print(f"\nRunning pipeline with {payload}\n")

        start = timeit.default_timer()

        if file_path is None and file is None:
            msg = "Please provide a file to process."
            raise ValueError(msg)

        if file_path is not None:
            with open(file_path, "rb") as file:
                files = {'file': (file_path, file, 'image/jpeg')}

                data = {
                    'image_url': ''
                }

                response = self.invoke_pipeline_step(lambda: requests.post(cfg.VPROCESSOR_OCR_ENDPOINT,
                                                                           data=data,
                                                                           files=files,
                                                                           timeout=180),
                                                     "Running OCR...",
                                                     local)
        else:
            files = {'file': (file.filename, file.file, file.content_type)}

            data = {
                'image_url': ''
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

        end = timeit.default_timer()
        print(f"Time to run OCR: {end - start}")

        start = timeit.default_timer()

        data = response.json()

        ResponseModel = self.invoke_pipeline_step(lambda: self.build_response_class(query_inputs, query_types),
                                                  "Building dynamic response class...",
                                                  local)

        prompt_template_str = """\
        """ + query + """\
        using this structured data, coming from OCR {document_data}.\
        """

        llm_ollama = self.invoke_pipeline_step(lambda: Ollama(model=cfg.LLM_VPROCESSOR,
                                                              base_url=cfg.OLLAMA_BASE_URL_VPROCESSOR,
                                                              temperature=0,
                                                              request_timeout=900),
                                               "Loading Ollama...",
                                               local)

        program = LLMTextCompletionProgram.from_defaults(
            output_cls=ResponseModel,
            prompt_template_str=prompt_template_str,
            llm=llm_ollama,
            verbose=True,
        )

        output = self.invoke_pipeline_step(lambda: program(document_data=data),
                                           "Running inference...",
                                           local)

        answer = self.beautify_json(output.model_dump_json())

        end = timeit.default_timer()

        print(f"\nJSON response:\n")
        print(answer + '\n')
        print('=' * 50)

        print(f"Time to retrieve answer: {end - start}")

        return answer

    def prepare_files(self, file_path, file):
        if file_path is not None:
            with open(file_path, "rb") as file:
                files = {'file': (file_path, file, 'image/jpeg')}

                data = {
                    'image_url': ''
                }
        else:
            files = {'file': (file.filename, file.file, file.content_type)}

            data = {
                'image_url': ''
            }
        return data, files


    # Function to safely evaluate type strings
    def safe_eval_type(self, type_str, context):
        try:
            return eval(type_str, {}, context)
        except NameError:
            raise ValueError(f"Type '{type_str}' is not recognized")

    def build_response_class(self, query_inputs, query_types_as_strings):
        # Controlled context for eval
        context = {
            'List': List,
            'str': str,
            'int': int,
            'float': float
            # Include other necessary types or typing constructs here
        }

        # Convert string representations to actual types
        query_types = [self.safe_eval_type(type_str, context) for type_str in query_types_as_strings]

        # Create fields dictionary
        fields = {name: (type_, ...) for name, type_ in zip(query_inputs, query_types)}

        DynamicModel = create_model('DynamicModel', **fields)

        return DynamicModel

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