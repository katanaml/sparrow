from abc import ABC, abstractmethod
from typing import Any
from typing import List
import warnings


warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)


# Abstract Interface
class Pipeline(ABC):
    @abstractmethod
    def run_pipeline(self,
                     agent: str,
                     query: str,
                     file_path: str,
                     options: List[str] = None,
                     crop_size: int = None,
                     debug_dir: str = None,
                     debug: bool = False,
                     local: bool = True) -> Any:
        pass


# Factory Method
def get_pipeline(agent_name: str) -> Pipeline:
    if agent_name == "sparrow-parse":
        from rag.agents.sparrow_parse.sparrow_parse import SparrowParsePipeline
        return SparrowParsePipeline()
    elif agent_name == "stocks":
        from rag.agents.instructor.stocks import Stocks
        return Stocks()
    else:
        raise ValueError(f"Unknown agent: {agent_name}")

