from embeddings.agents.interface import Ingest
from haystack.components.converters import PyPDFToDocument
from haystack.components.routers import FileTypeRouter
from haystack.components.preprocessors import DocumentSplitter, DocumentCleaner
from haystack.components.embedders import SentenceTransformersDocumentEmbedder
from haystack import Pipeline
from haystack_integrations.document_stores.weaviate.document_store import WeaviateDocumentStore
from haystack.components.writers import DocumentWriter
import timeit
import box
import yaml
from rich import print


# Import config vars
with open('config.yml', 'r', encoding='utf8') as ymlfile:
    cfg = box.Box(yaml.safe_load(ymlfile))


class HaystackIngest(Ingest):
    def run_ingest(self,
                   payload: str,
                   file_path: str,
                   index_name: str) -> None:
        print(f"\nRunning embeddings with {payload}\n")

        file_list = [file_path]

        start = timeit.default_timer()

        document_store = WeaviateDocumentStore(url=cfg.WEAVIATE_URL, collection_settings={"class": index_name})
        file_type_router = FileTypeRouter(mime_types=["application/pdf"])
        pdf_converter = PyPDFToDocument()

        document_cleaner = DocumentCleaner()
        document_splitter = DocumentSplitter(
            split_by="word",
            split_length=cfg.SPLIT_LENGTH_HAYSTACK,
            split_overlap=cfg.SPLIT_OVERLAP_HAYSTACK
        )

        document_embedder = SentenceTransformersDocumentEmbedder(model="sentence-transformers/all-MiniLM-L6-v2")
        document_writer = DocumentWriter(document_store)

        preprocessing_pipeline = Pipeline()
        preprocessing_pipeline.add_component(instance=file_type_router, name="file_type_router")
        preprocessing_pipeline.add_component(instance=pdf_converter, name="pypdf_converter")
        preprocessing_pipeline.add_component(instance=document_cleaner, name="document_cleaner")
        preprocessing_pipeline.add_component(instance=document_splitter, name="document_splitter")
        preprocessing_pipeline.add_component(instance=document_embedder, name="document_embedder")
        preprocessing_pipeline.add_component(instance=document_writer, name="document_writer")

        preprocessing_pipeline.connect("file_type_router.application/pdf", "pypdf_converter.sources")
        preprocessing_pipeline.connect("pypdf_converter", "document_cleaner")
        preprocessing_pipeline.connect("document_cleaner", "document_splitter")
        preprocessing_pipeline.connect("document_splitter", "document_embedder")
        preprocessing_pipeline.connect("document_embedder", "document_writer")

        # preprocessing_pipeline.draw("pipeline.png")

        preprocessing_pipeline.run({
            "file_type_router": {"sources": file_list}
        })

        print(f"Number of documents in document store: {document_store.count_documents()}")

        end = timeit.default_timer()
        print(f"Time to embeddings data: {end - start}")
