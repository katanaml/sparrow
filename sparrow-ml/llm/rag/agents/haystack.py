from rag.agents.interface import Pipeline as PipelineInterface
from typing import Any
from haystack.components.converters import PyPDFToDocument
from haystack.components.preprocessors import DocumentSplitter, DocumentCleaner
from haystack.components.embedders import SentenceTransformersDocumentEmbedder
from haystack import Pipeline
from haystack.document_stores.in_memory import InMemoryDocumentStore
from haystack.components.writers import DocumentWriter
from haystack.components.embedders import SentenceTransformersTextEmbedder
from haystack.components.retrievers.in_memory import InMemoryEmbeddingRetriever
from haystack.components.builders import PromptBuilder
from haystack_integrations.components.generators.ollama import OllamaGenerator
from pydantic import create_model
import json
from haystack import component
import pydantic
from typing import Optional, List
from pydantic import ValidationError
import timeit
import os
import box
import yaml
from rich import print
from rich.progress import Progress, SpinnerColumn, TextColumn


# Import config vars
with open('config.yml', 'r', encoding='utf8') as ymlfile:
    cfg = box.Box(yaml.safe_load(ymlfile))


class HaystackPipeline(PipelineInterface):
    def run_pipeline(self,
                     payload: str,
                     query_inputs: [str],
                     query_types: [str],
                     query: str,
                     file_path: str = None,
                     debug: bool = False,
                     local: bool = True) -> Any:
        print(f"\nRunning pipeline with {payload}\n")

        ResponseModel, json_schema = self.invoke_pipeline_step(lambda: self.build_response_class(query_inputs, query_types),
                                                               "Building dynamic response class...",
                                                               local)

        output_validator = self.invoke_pipeline_step(lambda: self.build_validator(ResponseModel),
                                                     "Building output validator...",
                                                     local)

        document_store = self.run_preprocessing_pipeline(local)

        answer = self.run_inference_pipeline(document_store, json_schema, output_validator, query, local)

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

        json_schema = DynamicModel.schema_json(indent=2)

        return DynamicModel, json_schema

    def build_validator(self, Invoice):
        @component
        class OutputValidator:
            def __init__(self, pydantic_model: pydantic.BaseModel):
                self.pydantic_model = pydantic_model
                self.iteration_counter = 0

            # Define the component output
            @component.output_types(valid_replies=List[str], invalid_replies=Optional[List[str]],
                                    error_message=Optional[str])
            def run(self, replies: List[str]):

                self.iteration_counter += 1

                ## Try to parse the LLM's reply ##
                # If the LLM's reply is a valid object, return `"valid_replies"`
                try:
                    output_dict = json.loads(replies[0])
                    # Disable data validation for now
                    # self.pydantic_model.model_validate(output_dict)
                    print(
                        f"OutputValidator at Iteration {self.iteration_counter}: Valid JSON from LLM - No need for looping."
                    )
                    return {"valid_replies": replies}

                # If the LLM's reply is corrupted or not valid, return "invalid_replies" and the "error_message" for LLM to try again
                except (ValueError, ValidationError) as e:
                    print(
                          f"\nOutputValidator at Iteration {self.iteration_counter}: Invalid JSON from LLM - Let's try again.\n"
                          f"Output from LLM:\n {replies[0]} \n"
                          f"Error from OutputValidator: {e}"
                    )
                    return {"invalid_replies": replies, "error_message": str(e)}

        output_validator = OutputValidator(pydantic_model=Invoice)

        return output_validator

    def run_preprocessing_pipeline(self, local):
        start = timeit.default_timer()

        file_list = [os.path.join(cfg.DATA_PATH, f) for f in os.listdir(cfg.DATA_PATH)
                     if os.path.isfile(os.path.join(cfg.DATA_PATH, f)) and not f.startswith('.')
                     and not f.lower().endswith('.jpg')]

        document_store = InMemoryDocumentStore()
        pdf_converter = PyPDFToDocument()

        document_cleaner = DocumentCleaner()
        document_splitter = DocumentSplitter(
            split_by=cfg.SPLIT_BY_HAYSTACK,
            split_length=cfg.SPLIT_LENGTH_HAYSTACK,
            split_overlap=cfg.SPLIT_OVERLAP_HAYSTACK
        )

        document_embedder = SentenceTransformersDocumentEmbedder(model=cfg.EMBEDDINGS_HAYSTACK,
                                                                 progress_bar=False)
        document_writer = DocumentWriter(document_store)

        preprocessing_pipe = Pipeline()
        preprocessing_pipe.add_component(instance=pdf_converter, name="pypdf_converter")
        preprocessing_pipe.add_component(instance=document_cleaner, name="document_cleaner")
        preprocessing_pipe.add_component(instance=document_splitter, name="document_splitter")
        preprocessing_pipe.add_component(instance=document_embedder, name="document_embedder")
        preprocessing_pipe.add_component(instance=document_writer, name="document_writer")

        preprocessing_pipe.connect("pypdf_converter", "document_cleaner")
        preprocessing_pipe.connect("document_cleaner", "document_splitter")
        preprocessing_pipe.connect("document_splitter", "document_embedder")
        preprocessing_pipe.connect("document_embedder", "document_writer")

        # preprocessing_pipeline.draw("pipeline.png")

        self.invoke_pipeline_step(lambda: preprocessing_pipe.run({
                                            "pypdf_converter": {"sources": file_list}
                                          }),
                                  "Running data ingestion pipeline...",
                                  local)

        print(f"\nNumber of documents in document store: {document_store.count_documents()}")

        end = timeit.default_timer()
        print(f"\nTime to ingest data: {end - start}\n")

        return document_store

    def run_inference_pipeline(self, document_store, json_schema, output_validator, query, local):
        start = timeit.default_timer()

        generator = OllamaGenerator(model=cfg.LLM_HAYSTACK,
                                    url=cfg.OLLAMA_BASE_URL_HAYSTACK + "/api/generate")

        template = """
        Given only the following document information, retrieve answer.
        Ignore your own knowledge. Format response with the following JSON schema:
        {{schema}}
        Make sure your response is a dict and not a list. Return only JSON, no additional text.

        Context:
        {% for document in documents %}
            {{ document.content }}
        {% endfor %}

        Question: {{ question }}?

        {% if invalid_replies and error_message %}
          You already created the following output in a previous attempt: {{invalid_replies}}
          However, this doesn't comply with the format requirements from above and triggered this Python exception: {{error_message}}
          Correct the output and try again. Just return the corrected output without any extra explanations.
        {% endif %}
        """

        text_embedder = SentenceTransformersTextEmbedder(model=cfg.EMBEDDINGS_HAYSTACK,
                                                         progress_bar=False)

        retriever = InMemoryEmbeddingRetriever(document_store=document_store, top_k=3)

        prompt_builder = PromptBuilder(template=template)

        pipe = Pipeline(max_loops_allowed=cfg.MAX_LOOPS_ALLOWED_HAYSTACK)
        pipe.add_component("embedder", text_embedder)
        pipe.add_component("retriever", retriever)
        pipe.add_component("prompt_builder", prompt_builder)
        pipe.add_component("llm", generator)
        pipe.add_component("output_validator", output_validator)

        pipe.connect("embedder.embedding", "retriever.query_embedding")
        pipe.connect("retriever", "prompt_builder.documents")
        pipe.connect("prompt_builder", "llm")
        pipe.connect("llm", "output_validator")
        # If a component has more than one output or input, explicitly specify the connections:
        pipe.connect("output_validator.invalid_replies", "prompt_builder.invalid_replies")
        pipe.connect("output_validator.error_message", "prompt_builder.error_message")

        question = (
            query
        )

        response = self.invoke_pipeline_step(
                            lambda: pipe.run(
                                        {
                                            "embedder": {"text": question},
                                            "prompt_builder": {"question": question, "schema": json_schema}
                                        }
                                    ),
            "Running inference pipeline...",
                          local)

        end = timeit.default_timer()

        valid_reply = response["output_validator"]["valid_replies"][0]
        valid_json = json.loads(valid_reply)
        print(f"\nJSON response:\n")
        print(valid_json)
        print('\n' + ('=' * 50))

        print(f"Time to retrieve answer: {end - start}")

        return valid_json

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