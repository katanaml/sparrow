from .interface import Ingest
import weaviate
from llama_index.core import StorageContext, SimpleDirectoryReader, ServiceContext, VectorStoreIndex
from llama_index.vector_stores.weaviate import WeaviateVectorStore
from llama_index.embeddings.langchain import LangchainEmbedding
from langchain.embeddings.huggingface import HuggingFaceEmbeddings
import box
import yaml
from rich.progress import Progress, SpinnerColumn, TextColumn
import timeit
from rich import print
import warnings


warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)


class LlamaIndexIngest(Ingest):
    def run_ingest(self, payload: str) -> None:
        print(f"\nRunning ingest with {payload}\n")

        # Import config vars
        with open('config.yml', 'r', encoding='utf8') as ymlfile:
            cfg = box.Box(yaml.safe_load(ymlfile))

        start = timeit.default_timer()

        client = self.invoke_pipeline_step(lambda: weaviate.Client(cfg.WEAVIATE_URL), "Connecting to Weaviate...")

        documents = self.invoke_pipeline_step(lambda: self.load_documents(cfg.DATA_PATH),
                                         "Loading documents...")

        embeddings = self.invoke_pipeline_step(lambda: self.load_embedding_model(cfg.EMBEDDINGS),
                                          "Loading embedding model...")

        index = self.invoke_pipeline_step(lambda: self.build_index(client, embeddings, documents, cfg.INDEX_NAME, cfg.CHUNK_SIZE),
                                     "Building index...")

        end = timeit.default_timer()
        print(f"\nTime to ingest data: {end - start}\n")

    def load_documents(self, docs_path):
        # Add support to process multiple documents
        documents = SimpleDirectoryReader(docs_path, required_exts=[".pdf", ".PDF"]).load_data()
        print(f"\nLoaded {len(documents)} documents")
        print(f"\nFirst document: {documents[0]}")
        print("\nFirst document content:\n")
        print(documents[0])
        print()
        return documents

    def load_embedding_model(self, model_name):
        embeddings = LangchainEmbedding(
            HuggingFaceEmbeddings(model_name=model_name)
        )
        return embeddings

    def build_index(self, weaviate_client, embed_model, documents, index_name, chunk_size):
        # Delete index if it already exists, to avoid data corruption
        weaviate_client.schema.delete_class(index_name)

        service_context = ServiceContext.from_defaults(embed_model=embed_model,
                                                       llm=None,
                                                       chunk_size=chunk_size)
        vector_store = WeaviateVectorStore(weaviate_client=weaviate_client, index_name=index_name)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)

        index = VectorStoreIndex.from_documents(
            documents,
            service_context=service_context,
            storage_context=storage_context
        )

        return index

    def invoke_pipeline_step(self, task_call, task_description):
        with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=False,
        ) as progress:
            progress.add_task(description=task_description, total=None)
            ret = task_call()
        return ret