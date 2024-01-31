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
def get_pipeline(plugin_name: str) -> Pipeline:
    if plugin_name == "LlamaIndex":
        from .llama_index import LlamaIndexPipeline
        return LlamaIndexPipeline()
    elif plugin_name == "Haystack":
        from .haystack import HaystackPipeline
        return HaystackPipeline()
    else:
        raise ValueError(f"Unknown plugin: {plugin_name}")

