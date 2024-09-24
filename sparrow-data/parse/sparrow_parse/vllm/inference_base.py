from abc import ABC, abstractmethod

class ModelInference(ABC):
    @abstractmethod
    def inference(self, input_data):
        """This method should be implemented by subclasses."""
        pass
