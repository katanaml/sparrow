from abc import ABC, abstractmethod
import warnings


warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)


# Abstract Interface
class Ingest(ABC):
    @abstractmethod
    def run_ingest(self,
                   payload: str,
                   file_path: str,
                   index_name: str) -> None:
        pass


# Factory Method
def get_ingest(agent_name: str) -> Ingest:
    if agent_name == "llamaindex":
        from .llamaindex import LlamaIndexIngest
        return LlamaIndexIngest()
    elif agent_name == "haystack":
        from .haystack import HaystackIngest
        return HaystackIngest()
    else:
        raise ValueError(f"Unknown agent: {agent_name}")

