from abc import ABC, abstractmethod

from typing import Any


class VectorStore(ABC):
    """
    Base class for embedding functions.
    """

    @abstractmethod
    def add_data(self, *args, **kwargs) -> Any:
        """
        Add data to the vector store.
        """
        pass

    @abstractmethod
    def query_data(self, *args, **kwargs) -> Any:
        """
        Query certain data through from the DB.
        """
        pass
    