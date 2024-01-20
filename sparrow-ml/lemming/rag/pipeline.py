from llama_index import VectorStoreIndex, ServiceContext
from llama_index.embeddings import LangchainEmbedding
from langchain.embeddings.huggingface import HuggingFaceEmbeddings
from llama_index.llms import Ollama
from llama_index.vector_stores import WeaviateVectorStore
import weaviate
from pydantic import create_model
from typing import List
import box
import yaml
from rich.progress import Progress, SpinnerColumn, TextColumn


# Function to safely evaluate type strings
def safe_eval_type(type_str, context):
    try:
        return eval(type_str, {}, context)
    except NameError:
        raise ValueError(f"Type '{type_str}' is not recognized")


def build_response_class(query_inputs, query_types_as_strings):
    # Controlled context for eval
    context = {
        'List': List,
        'str': str,
        'int': int,
        'float': float
        # Include other necessary types or typing constructs here
    }

    # Convert string representations to actual types
    query_types = [safe_eval_type(type_str, context) for type_str in query_types_as_strings]

    # Create fields dictionary
    fields = {name: (type_, ...) for name, type_ in zip(query_inputs, query_types)}

    DynamicModel = create_model('DynamicModel', **fields)

    return DynamicModel


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


def build_rag_pipeline(query_inputs, query_types, debug=False, local=True):
    # Import config vars
    with open('config.yml', 'r', encoding='utf8') as ymlfile:
        cfg = box.Box(yaml.safe_load(ymlfile))

    client = invoke_pipeline_step(lambda: weaviate.Client(cfg.WEAVIATE_URL),
                                  "Connecting to Weaviate...",
                                  local)

    llm = invoke_pipeline_step(lambda: Ollama(model=cfg.LLM, base_url=cfg.OLLAMA_BASE_URL, temperature=0,
                                              request_timeout=900),
                               "Loading Ollama...",
                               local)

    embeddings = invoke_pipeline_step(lambda: load_embedding_model(model_name=cfg.EMBEDDINGS),
                                      "Loading embedding model...",
                                      local)

    index = invoke_pipeline_step(lambda: build_index(cfg.CHUNK_SIZE, llm, embeddings, client, cfg.INDEX_NAME),
                                 "Building index...",
                                 local)

    ResponseModel = invoke_pipeline_step(lambda: build_response_class(query_inputs, query_types),
                                         "Building dynamic response class...",
                                         local)

    # may want to try with similarity_top_k=5, default is 2
    query_engine = invoke_pipeline_step(lambda: index.as_query_engine(
                                            streaming=False,
                                            output_cls=ResponseModel,
                                            response_mode="compact"
                                        ),
                                        "Constructing query engine...",
                                        local)

    return query_engine


def invoke_pipeline_step(task_call, task_description, local):
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
