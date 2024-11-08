from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple

import _import_root  # noqa : E402

from universa.memory.chromadb.chromadb import ChromaDB
from universa.memory.embedding_functions.chromadb_default import ChromaDBDefaultEF


class SelectionAlgorithm(ABC):
    """
    All solutions must implement this interface.
    """
    def __init__(self, agents: List[Dict[str, Any]], ids: List[str]) -> None:
        self.agents = agents
        self.ids = ids
        self.initialize(agents, ids)

    @abstractmethod
    def select(self, query: str, **kwargs) -> Tuple[str, str]:
        # TODO: Add agent selection logic here
        ...

    @abstractmethod
    def initialize(self, agents: List[Dict[str, Any]], ids: List[str]) -> str:
        # TODO: Initialize vectorstore
        ...


class ExampleAlgorithm(SelectionAlgorithm):
    """
    Example selection algorithm.
    """
    def select(self, query: str) -> Tuple[str, str]:
        results = self.chroma.query_data(query)
        _id = results['ids'][0][0]
        return _id, self.agents[self.ids.index(_id)]['name']
    
    def initialize(self, agents: List[Dict[str, Any]], ids: List[str]) -> None:
        self.chroma = ChromaDB(
            embedding_function=ChromaDBDefaultEF(),
            collection_name="example_collection"
        )

        agent_data = [agent['description'] + "\n\n" + agent['system_prompt'] for agent in agents]
        self.chroma.add_data(
            documents=agent_data,
            ids=ids
        )
