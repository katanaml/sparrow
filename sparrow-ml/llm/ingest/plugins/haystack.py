from ingest.plugins.interface import Ingest
from haystack.components.converters import PyPDFToDocument
from haystack.components.routers import FileTypeRouter
from haystack.components.preprocessors import DocumentSplitter, DocumentCleaner
from haystack.components.embedders import SentenceTransformersDocumentEmbedder
from haystack.pipeline import Pipeline
from haystack_integrations.document_stores.chroma import ChromaDocumentStore
from haystack.components.writers import DocumentWriter
import timeit
import os
import box
import yaml
from rich import print


# Import config vars
with open('config.yml', 'r', encoding='utf8') as ymlfile:
    cfg = box.Box(yaml.safe_load(ymlfile))


class HaystackIngest(Ingest):
    def run_ingest(self, payload: str) -> None:
        print(f"\nRunning ingest with {payload}\n")

        file_list = [os.path.join(cfg.DATA_PATH, f) for f in os.listdir(cfg.DATA_PATH)
                     if os.path.isfile(os.path.join(cfg.DATA_PATH, f)) and not f.startswith('.')
                     and not f.lower().endswith('.jpg')]

        start = timeit.default_timer()

        document_store = ChromaDocumentStore()
        file_type_router = FileTypeRouter(mime_types=["application/pdf"])
        pdf_converter = PyPDFToDocument()

        document_cleaner = DocumentCleaner()
        document_splitter = DocumentSplitter(
            split_by="word",
            split_length=150,
            split_overlap=50
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
        print("Haystack ingest is not used, you should run inference directly. Ingest will execute as a part of the inference.")

        end = timeit.default_timer()
        print(f"Time to prepare embeddings: {end - start}")
