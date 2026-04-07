from abc import ABC, abstractmethod

class BaseLLM(ABC):

    @abstractmethod
    def call_llm(self) -> str:
        """
        Abstract method to call the LLM and return a response.
        Must be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement the call_llm() method.")


