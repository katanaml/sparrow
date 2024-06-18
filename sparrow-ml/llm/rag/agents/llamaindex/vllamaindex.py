from rag.agents.interface import Pipeline
from rich.progress import Progress, SpinnerColumn, TextColumn
from typing import Any
from pydantic import create_model
from typing import List
import warnings
import box
import yaml
import timeit
from rich import print
from llama_index.core import SimpleDirectoryReader
from llama_index.multi_modal_llms.ollama import OllamaMultiModal
from llama_index.core.program import MultiModalLLMCompletionProgram
from llama_index.core.output_parsers import PydanticOutputParser


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

        start = timeit.default_timer()

        if file_path is None:
            raise ValueError("File path is required for vllamaindex pipeline")

        mm_model = self.invoke_pipeline_step(lambda: OllamaMultiModal(model=cfg.LLM_VLLAMAINDEX),
                                             "Loading Ollama MultiModal...",
                                             local)

        # load as image documents
        image_documents = self.invoke_pipeline_step(lambda: SimpleDirectoryReader(input_files=[file_path],
                                                                                  required_exts=[".jpg", ".JPG",
                                                                                                 ".JPEG"]).load_data(),
                                                    "Loading image documents...",
                                                    local)

        ResponseModel = self.invoke_pipeline_step(lambda: self.build_response_class(query_inputs, query_types),
                                                  "Building dynamic response class...",
                                                  local)

        prompt_template_str = """\
        {query_str}

        Return the answer as a Pydantic object. The Pydantic schema is given below:

        """
        mm_program = MultiModalLLMCompletionProgram.from_defaults(
            output_parser=PydanticOutputParser(ResponseModel),
            image_documents=image_documents,
            prompt_template_str=prompt_template_str,
            multi_modal_llm=mm_model,
            verbose=True,
        )

        try:
            response = self.invoke_pipeline_step(lambda: mm_program(query_str=query),
                                                 "Running inference...",
                                                 local)
        except ValueError as e:
            print(f"Error: {e}")
            msg = 'Inference failed'
            return '{"answer": "' + msg + '"}'

        end = timeit.default_timer()

        print(f"\nJSON response:\n")
        for res in response:
            print(res)
        print('=' * 50)

        print(f"Time to retrieve answer: {end - start}")

        return response


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


