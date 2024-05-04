from rag.agents.interface import Pipeline
from openai import OpenAI
import instructor
from sparrow_parse.extractor.file_processor import FileProcessor
from pydantic import create_model
from typing import List
from rich.progress import Progress, SpinnerColumn, TextColumn
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

        processor = FileProcessor()
        content = processor.extract_data(file_path, strategy, model_name, options, local, debug)

        # with open("data/invoice_1.txt", 'r') as file:
        #     content = file.read()

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
