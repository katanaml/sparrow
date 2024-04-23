from rag.agents.interface import Pipeline
from openai import OpenAI
import instructor
from unstructured.partition.pdf import partition_pdf
from unstructured.partition.image import partition_image
from unstructured.staging.base import elements_to_json
from pydantic import create_model
from typing import List
from rich.progress import Progress, SpinnerColumn, TextColumn
import tempfile
import os
import json
import timeit
from rich import print
from typing import Any
import box
import yaml
import warnings


warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)


# Import config vars
with open('config.yml', 'r', encoding='utf8') as ymlfile:
    cfg = box.Box(yaml.safe_load(ymlfile))


class InstructorPipeline(Pipeline):
    def run_pipeline(self,
                     payload: str,
                     query_inputs: [str],
                     query_types: [str],
                     query: str,
                     file_path: str,
                     index_name: str,
                     options: str = None,
                     debug: bool = False,
                     local: bool = True) -> Any:
        print(f"\nRunning pipeline with {payload}\n")

        # Import config vars
        with open('config.yml', 'r', encoding='utf8') as ymlfile:
            cfg = box.Box(yaml.safe_load(ymlfile))

        start = timeit.default_timer()

        strategy = cfg.STRATEGY_INSTRUCTOR
        model_name = cfg.MODEL_INSTRUCTOR

        # check if string options contains word table
        extract_tables = False
        if options is not None and "tables" in options:
            extract_tables = True

        # Extracts the elements from the PDF
        elements = self.invoke_pipeline_step(
            lambda: self.process_file(file_path, strategy, model_name),
            "Extracting elements from the document...",
            local
        )

        if debug:
            new_extension = 'json'  # You can change this to any extension you want
            new_file_path = self.change_file_extension(file_path, new_extension)

            content = self.invoke_pipeline_step(
                lambda: self.load_text_data(elements, new_file_path, extract_tables),
                "Loading text data...",
                local
            )
        else:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_file_path = os.path.join(temp_dir, "file_data.json")

                content = self.invoke_pipeline_step(
                    lambda: self.load_text_data(elements, temp_file_path, extract_tables),
                    "Loading text data...",
                    local
                )

        if debug:
            print(f"\nContent: {content}\n")

        ResponseModel = self.invoke_pipeline_step(lambda: self.build_response_class(query_inputs, query_types),
                                                  "Building dynamic response class...",
                                                  local)

        answer = self.invoke_pipeline_step(
            lambda: self.execute_query(query, content, ResponseModel),
            "Executing query...",
            local
        )

        end = timeit.default_timer()

        print(f"\nJSON response:\n")
        print(answer + '\n')
        print('=' * 50)

        print(f"Time to retrieve answer: {end - start}")

        return answer

    def execute_query(self, query, content, ResponseModel):
        client = instructor.from_openai(
            OpenAI(
                base_url=cfg.OLLAMA_BASE_URL_INSTRUCTOR,
                api_key="ollama",
            ),
            mode=instructor.Mode.JSON,
        )

        resp = client.chat.completions.create(
            model=cfg.LLM_INSTRUCTOR,
            messages=[
                {
                    "role": "user",
                    "content": f"{query} from the following content {content}."
                }
            ],
            response_model=ResponseModel,
            max_retries=3
        )

        answer = resp.model_dump_json(indent=4)

        return answer

    def process_file(self, file_path, strategy, model_name):
        elements = None

        if file_path.lower().endswith('.pdf'):
            elements = partition_pdf(
                filename=file_path,
                strategy=strategy,
                infer_table_structure=True,
                model_name=model_name
            )
        elif file_path.lower().endswith(('.jpg', '.jpeg', '.png')):
            elements = partition_image(
                filename=file_path,
                strategy=strategy,
                infer_table_structure=True,
                model_name=model_name
            )

        return elements

    def load_text_data(self, elements, file_path, extract_tables):
        elements_to_json(elements, filename=file_path)
        text_file = self.process_json_file(file_path, extract_tables)

        with open(text_file, 'r') as file:
            content = file.read()

        return content

    def process_json_file(self, input_data, extract_tables):
        # Read the JSON file
        with open(input_data, 'r') as file:
            data = json.load(file)

        # Iterate over the JSON data and extract required table elements
        extracted_elements = []
        for entry in data:
            if entry["type"] == "Table":
                extracted_elements.append(entry["metadata"]["text_as_html"])
            elif entry["type"] == "Title" and extract_tables is False:
                extracted_elements.append(entry["text"])
            elif entry["type"] == "NarrativeText" and extract_tables is False:
                extracted_elements.append(entry["text"])

        # Write the extracted elements to the output file
        new_extension = 'txt'  # You can change this to any extension you want
        new_file_path = self.change_file_extension(input_data, new_extension)
        with open(new_file_path, 'w') as output_file:
            for element in extracted_elements:
                output_file.write(element + "\n\n")  # Adding two newlines for separation

        return new_file_path

    def change_file_extension(self, file_path, new_extension):
        # Check if the new extension starts with a dot and add one if not
        if not new_extension.startswith('.'):
            new_extension = '.' + new_extension

        # Split the file path into two parts: the base (everything before the last dot) and the extension
        # If there's no dot in the filename, it'll just return the original filename without an extension
        base = file_path.rsplit('.', 1)[0]

        # Concatenate the base with the new extension
        new_file_path = base + new_extension

        return new_file_path

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
