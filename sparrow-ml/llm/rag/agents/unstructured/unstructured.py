from rag.agents.interface import Pipeline
import uuid
import weaviate
from weaviate.util import get_valid_uuid
from unstructured.chunking.title import chunk_by_title
from unstructured.documents.elements import DataSourceMetadata
from unstructured.partition.json import partition_json
from sentence_transformers import SentenceTransformer
from langchain.vectorstores.weaviate import Weaviate
from langchain.prompts import PromptTemplate
from langchain_community.llms import Ollama
import tempfile
import subprocess
import os
from typing import List, Dict
import warnings
import box
import yaml
import timeit
import json
from rich import print
from typing import Any
from rich.progress import Progress, SpinnerColumn, TextColumn
from pydantic.v1 import create_model


warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)


# Import config vars
with open('config.yml', 'r', encoding='utf8') as ymlfile:
    cfg = box.Box(yaml.safe_load(ymlfile))


class UnstructuredPipeline(Pipeline):
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

        if len(query_inputs) == 1:
            raise ValueError("Please provide more than one query input")

        start = timeit.default_timer()

        output_dir = cfg.OUTPUT_DIR_UNSTRUCTURED
        input_dir = cfg.INPUT_DIR_UNSTRUCTURED
        weaviate_url = cfg.WEAVIATE_URL_UNSTRUCTURED
        embedding_model_name = cfg.EMBEDDINGS_UNSTRUCTURED
        device = cfg.DEVICE_UNSTRUCTURED

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_input_dir = os.path.join(temp_dir, input_dir)
            temp_output_dir = os.path.join(temp_dir, output_dir) if debug is False else output_dir

            if debug:
                print(f"Copying {file_path} to {temp_input_dir}")
            os.makedirs(temp_input_dir, exist_ok=True)
            os.system(f"cp {file_path} {temp_input_dir}")

            os.makedirs(temp_output_dir, exist_ok=True)

            files = self.invoke_pipeline_step(
                lambda: self.process_files(temp_output_dir, temp_input_dir),
                "Processing file with unstructured...",
                local
            )

            vectorstore, embedding_model = self.invoke_pipeline_step(
                lambda: self.build_vector_store(weaviate_url, embedding_model_name, device, files, debug),
                "Building vector store...",
                local
            )

        llm = self.invoke_pipeline_step(
            lambda: Ollama(model=cfg.LLM_UNSTRUCTURED,
                           base_url=cfg.BASE_URL_UNSTRUCTURED),
            "Initializing Ollama...",
            local
        )

        raw_result, similar_docs = self.invoke_pipeline_step(
            lambda: self.question_answer(query, vectorstore, embedding_model, device, llm),
            "Answering question...",
            local
        )

        answer = self.invoke_pipeline_step(
            lambda: self.validate_output(raw_result, query_inputs, query_types),
            "Validating output...",
            local
        )

        if debug:
            print("\n\n\n-------------------------")
            print(f"QUERY: {query}")
            print("\n\n\n-------------------------")
            print(f"Answer: {answer}")
            print("\n\n\n-------------------------")
            for index, result in enumerate(similar_docs):
                print(f"\n\n-- RESULT {index + 1}:\n")
                print(result)

        end = timeit.default_timer()

        print(f"\nJSON response:\n")
        print(answer + '\n')
        print('=' * 50)

        print(f"Time to retrieve answer: {end - start}")

        return answer

    def process_files(self, temp_output_dir, temp_input_dir):
        self.process_local(output_dir=temp_output_dir, num_processes=2, input_path=temp_input_dir)
        files = self.get_result_files(temp_output_dir)
        return files

    def build_vector_store(self, weaviate_url, embedding_model_name, device, files, debug):
        client = self.create_local_weaviate_client(db_url=weaviate_url)
        my_schema = self.get_schema()
        self.upload_schema(my_schema, weaviate=client)

        vectorstore = Weaviate(client, "Doc", "text")
        embedding_model = SentenceTransformer(embedding_model_name, device=device)

        self.add_data_to_weaviate(
            debug,
            files=files,
            client=client,
            embedding_model=embedding_model,
            device=device,
            chunk_under_n_chars=cfg.CHUNK_UNDER_N_CHARS_UNSTRUCTURED,
            chunk_new_after_n_chars=cfg.CHUNK_NEW_AFTER_N_CHARS_UNSTRUCTURED
        )

        if debug:
            print(self.count_documents(client=client)['data']['Aggregate']['Doc'])

        return vectorstore, embedding_model

    def process_local(self, output_dir: str, num_processes: int, input_path: str):
        command = [
            "unstructured-ingest",
            "local",
            "--input-path", input_path,
            "--output-dir", output_dir,
            "--num-processes", str(num_processes),
            "--recursive",
            "--verbose",
        ]

        # Run the command
        process = subprocess.Popen(command, stdout=subprocess.PIPE)
        output, error = process.communicate()

        # Print output
        if process.returncode == 0:
            print('Command executed successfully. Output:')
            print(output.decode())
        else:
            print('Command failed. Error:')
            print(error.decode())

    def get_result_files(self, folder_path) -> List[Dict]:
        file_list = []
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.endswith('.json'):
                    file_path = os.path.join(root, file)
                    file_list.append(file_path)
        return file_list


    def create_local_weaviate_client(self, db_url: str):
        return weaviate.Client(
            url=db_url,
        )

    def get_schema(self, vectorizer: str = "none"):
        return {
            "classes": [
                {
                    "class": "Doc",
                    "description": "A generic document class",
                    "vectorizer": vectorizer,
                    "properties": [
                        {
                            "name": "last_modified",
                            "dataType": ["text"],
                            "description": "Last modified date for the document",
                        },
                        {
                            "name": "player",
                            "dataType": ["text"],
                            "description": "Player related to the document",
                        },
                        {
                            "name": "position",
                            "dataType": ["text"],
                            "description": "Player Position related to the document",
                        },
                        {
                            "name": "text",
                            "dataType": ["text"],
                            "description": "Text content for the document",
                        },
                    ],
                },
            ],
        }

    def upload_schema(self, my_schema, weaviate):
        weaviate.schema.delete_all()
        weaviate.schema.create(my_schema)

    def count_documents(self, client: weaviate.Client) -> Dict:
        response = (
            client.query
            .aggregate("Doc")
            .with_meta_count()
            .do()
        )
        count = response
        return count

    def compute_embedding(self, chunk_text: List[str], embedding_model, device):
        embeddings = embedding_model.encode(chunk_text, device=device)
        return embeddings

    def get_chunks(self, elements, embedding_model, device, chunk_under_n_chars=500, chunk_new_after_n_chars=1500):
        for element in elements:
            if not type(element.metadata.data_source) is DataSourceMetadata:
                delattr(element.metadata, "data_source")

            if hasattr(element.metadata, "coordinates"):
                delattr(element.metadata, "coordinates")

        chunks = chunk_by_title(
            elements,
            combine_text_under_n_chars=chunk_under_n_chars,
            new_after_n_chars=chunk_new_after_n_chars
        )

        for i in range(len(chunks)):
            chunks[i] = {"last_modified": chunks[i].metadata.last_modified, "text": chunks[i].text}

        chunk_texts = [x['text'] for x in chunks]
        embeddings = self.compute_embedding(chunk_texts, embedding_model, device)
        return chunks, embeddings

    def add_data_to_weaviate(self, debug, files, client, embedding_model, device, chunk_under_n_chars=500, chunk_new_after_n_chars=1500):
        for filename in files:
            try:
                elements = partition_json(filename=filename)
                chunks, embeddings = self.get_chunks(elements, embedding_model, device, chunk_under_n_chars, chunk_new_after_n_chars)
            except IndexError as e:
                print(e)
                continue

            if debug:
                print(f"Uploading {len(chunks)} chunks for {str(filename)}.")

            for i, chunk in enumerate(chunks):
                client.batch.add_data_object(
                    data_object=chunk,
                    class_name="doc",
                    uuid=get_valid_uuid(uuid.uuid4()),
                    vector=embeddings[i]
                )

        client.batch.flush()

    def question_answer(self, question: str, vectorstore: Weaviate, embedding_model, device, llm):
        embedding = self.compute_embedding(question, embedding_model, device)
        similar_docs = vectorstore.max_marginal_relevance_search_by_vector(embedding)
        content = [x.page_content for x in similar_docs]
        prompt_template = PromptTemplate.from_template(
            """\
            Given context about the subject, answer the question based on the context provided to the best of your ability.
            Context: {context}
            Question:
            {question}
            Answer:
            """
        )
        prompt = prompt_template.format(context=content, question=question)
        answer = llm(prompt)
        return answer, similar_docs

    def validate_output(self, raw_result, query_inputs, query_types):
        if raw_result is None:
            return {}

        clean_str = raw_result.replace('<|im_end|>', '')

        # Convert the cleaned string to a dictionary
        response_dict = json.loads(clean_str)

        ResponseModel = self.build_response_class(query_inputs, query_types)

        # Validate and create a Pydantic model instance
        validated_response = ResponseModel(**response_dict)

        # Convert the model instance to JSON
        answer = self.beautify_json(validated_response.json())

        return answer

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
