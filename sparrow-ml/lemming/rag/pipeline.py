from llama_index import VectorStoreIndex, ServiceContext
from llama_index.embeddings import LangchainEmbedding
from langchain.embeddings.huggingface import HuggingFaceEmbeddings
from llama_index.llms import Ollama
from llama_index.vector_stores import WeaviateVectorStore
import weaviate
from pydantic import BaseModel
from typing import List
import box
import yaml


class InvoiceInfo(BaseModel):
    invoice_number: int
    invoice_date: str
    client_name: str
    client_address: str
    client_tax_id: str
    seller_name: str
    seller_address: str
    seller_tax_id: str
    iban: str
    names_of_invoice_items: List[str]
    gross_worth_of_invoice_items: List[float]
    total_gross_worth: str


def load_embedding_model(model_name):
    embeddings = LangchainEmbedding(
        HuggingFaceEmbeddings(model_name=model_name)
    )
    return embeddings


def build_index(chunk_size, llm, embed_model, weaviate_client, index_name):
    service_context = ServiceContext.from_defaults(
        chunk_size=chunk_size,
        llm=llm,
        embed_model=embed_model
    )

    vector_store = WeaviateVectorStore(weaviate_client=weaviate_client, index_name=index_name)

    index = VectorStoreIndex.from_vector_store(
        vector_store, service_context=service_context
    )

    return index


def build_rag_pipeline(debug=False):
    # Import config vars
    with open('config.yml', 'r', encoding='utf8') as ymlfile:
        cfg = box.Box(yaml.safe_load(ymlfile))

    print("Connecting to Weaviate")
    client = weaviate.Client(cfg.WEAVIATE_URL)

    print("Loading Ollama...")
    llm = Ollama(model=cfg.LLM, base_url=cfg.OLLAMA_BASE_URL, temperature=0)

    print("Loading embedding model...")
    embeddings = load_embedding_model(model_name=cfg.EMBEDDINGS)

    print("Building index...")
    index = build_index(cfg.CHUNK_SIZE, llm, embeddings, client, cfg.INDEX_NAME)

    print("Constructing query engine...")

    query_engine = index.as_query_engine(
        streaming=False,
        output_cls=InvoiceInfo,
        response_mode="compact"
    )

    # query_engine = index.as_query_engine(
    #     streaming=False
    # )

    return query_engine
