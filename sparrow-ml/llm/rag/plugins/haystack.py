from rag.plugins.interface import Pipeline as PipelineInterface
from typing import Any
from haystack.components.converters import PyPDFToDocument
from haystack.components.preprocessors import DocumentSplitter, DocumentCleaner
from haystack.components.embedders import SentenceTransformersDocumentEmbedder
from haystack.pipeline import Pipeline
from haystack.document_stores.in_memory import InMemoryDocumentStore
from haystack.components.writers import DocumentWriter
from haystack.components.embedders import SentenceTransformersTextEmbedder
from haystack.components.retrievers.in_memory import InMemoryEmbeddingRetriever
from haystack.components.builders import PromptBuilder
from haystack_integrations.components.generators.ollama import OllamaGenerator
from typing import List
from colorama import Fore
import json
from pydantic import BaseModel
from haystack import component
import pydantic
from typing import Optional, List
from pydantic import ValidationError
import timeit
import os
import box
import yaml
from rich import print


# Import config vars
with open('config.yml', 'r', encoding='utf8') as ymlfile:
    cfg = box.Box(yaml.safe_load(ymlfile))


class HaystackPipeline(PipelineInterface):
    def run_pipeline(self,
                     payload: str,
                     query_inputs: [str],
                     query_types: [str],
                     query: str,
                     debug: bool = False,
                     local: bool = True) -> Any:
        print(f"\nRunning pipeline with {payload}\n")

        class Invoice(BaseModel):
            invoice_number: str

        json_schema = Invoice.schema_json(indent=2)

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
                    self.pydantic_model.model_validate(output_dict)
                    print(
                        Fore.GREEN
                        + f"OutputValidator at Iteration {self.iteration_counter}: Valid JSON from LLM - No need for looping: {replies[0]}"
                    )
                    return {"valid_replies": replies}

                # If the LLM's reply is corrupted or not valid, return "invalid_replies" and the "error_message" for LLM to try again
                except (ValueError, ValidationError) as e:
                    print(
                        Fore.RED
                        + f"OutputValidator at Iteration {self.iteration_counter}: Invalid JSON from LLM - Let's try again.\n"
                          f"Output from LLM:\n {replies[0]} \n"
                          f"Error from OutputValidator: {e}"
                    )
                    return {"invalid_replies": replies, "error_message": str(e)}

        output_validator = OutputValidator(pydantic_model=Invoice)

        file_list = [os.path.join(cfg.DATA_PATH, f) for f in os.listdir(cfg.DATA_PATH)
                     if os.path.isfile(os.path.join(cfg.DATA_PATH, f)) and not f.startswith('.')
                     and not f.lower().endswith('.jpg')]

        start = timeit.default_timer()

        document_store = InMemoryDocumentStore()
        pdf_converter = PyPDFToDocument()

        document_cleaner = DocumentCleaner()
        document_splitter = DocumentSplitter(
            split_by="sentence",
            split_length=10,
            split_overlap=2
        )

        document_embedder = SentenceTransformersDocumentEmbedder(model="sentence-transformers/all-MiniLM-L6-v2")
        document_writer = DocumentWriter(document_store)

        preprocessing_pipeline = Pipeline()
        preprocessing_pipeline.add_component(instance=pdf_converter, name="pypdf_converter")
        preprocessing_pipeline.add_component(instance=document_cleaner, name="document_cleaner")
        preprocessing_pipeline.add_component(instance=document_splitter, name="document_splitter")
        preprocessing_pipeline.add_component(instance=document_embedder, name="document_embedder")
        preprocessing_pipeline.add_component(instance=document_writer, name="document_writer")

        preprocessing_pipeline.connect("pypdf_converter", "document_cleaner")
        preprocessing_pipeline.connect("document_cleaner", "document_splitter")
        preprocessing_pipeline.connect("document_splitter", "document_embedder")
        preprocessing_pipeline.connect("document_embedder", "document_writer")

        # preprocessing_pipeline.draw("pipeline.png")

        preprocessing_pipeline.run({
            "pypdf_converter": {"sources": file_list}
        })

        print(f"Number of documents in document store: {document_store.count_documents()}")

        end = timeit.default_timer()
        print(f"Time to ingest data: {end - start}")

        start = timeit.default_timer()

        generator = OllamaGenerator(model="starling-lm:7b-alpha-q4_K_M",
                                    url="http://192.168.68.107:11434/api/generate")

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
        """

        pipe = Pipeline(max_loops_allowed=3)
        pipe.add_component("embedder", SentenceTransformersTextEmbedder(model="sentence-transformers/all-MiniLM-L6-v2"))
        pipe.add_component("retriever", InMemoryEmbeddingRetriever(document_store=document_store, top_k=3))
        pipe.add_component("prompt_builder", PromptBuilder(template=template))
        pipe.add_component("llm", generator)
        pipe.add_component("output_validator", output_validator)

        pipe.connect("embedder.embedding", "retriever.query_embedding")
        pipe.connect("retriever", "prompt_builder.documents")
        pipe.connect("prompt_builder", "llm")
        pipe.connect("llm", "output_validator")

        question = (
            "retrieve invoice_number"
        )

        response = pipe.run(
            {
                "embedder": {"text": question},
                "prompt_builder": {"question": question, "schema": json_schema}
            }
        )

        valid_reply = response["output_validator"]["valid_replies"][0]
        print(valid_reply)


        end = timeit.default_timer()
        print(f"Time to retrieve answer: {end - start}")

        return '{"answer": "Not implemented yet"}'
