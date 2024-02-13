from abc import ABC, abstractmethod
from typing import Any
import warnings


warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)


# Abstract Interface
class Pipeline(ABC):
    @abstractmethod
    def run_pipeline(self,
                     payload: str,
                     query_inputs: [str],
                     query_types: [str],
                     query: str,
                     debug: bool = False,
                     local: bool = True) -> Any:
        pass


# Factory Method
def get_pipeline(agent_name: str) -> Pipeline:
    if agent_name == "LlamaIndex":
        from .llama_index import LlamaIndexPipeline
        return LlamaIndexPipeline()
    elif agent_name == "Haystack":
        from .haystack import HaystackPipeline
        return HaystackPipeline()
    elif agent_name == "LlamaIndex_Llava":
        from .llama_index_multimodal_ollama import LlavaPipeline
        return LlavaPipeline()
    else:
        raise ValueError(f"Unknown agent: {agent_name}")

