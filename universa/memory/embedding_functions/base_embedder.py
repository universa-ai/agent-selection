from abc import ABC, abstractmethod

from typing import List


class BaseEmbeddingFunction(ABC):
    """
    Base class for embedding functions.
    """
    
    @abstractmethod
    def create_embeddings(self, texts: List[str], *args, **kwargs) -> List[List[float]]:
        """
        Create embeddings for the given input.
        """
        pass
    