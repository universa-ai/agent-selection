import chromadb
from chromadb.config import Settings
from chromadb.api.types import (
    Where,
    GetResult,
    QueryResult,
)

from ..vector_store import VectorStore
from ..embedding_functions.base_embedder import BaseEmbeddingFunction

from ...utils._types import *
from ...utils.logs import get_logger


class ChromaDB(VectorStore):
    """
    ChromaDB is an example of a vector-store class implementation.

    See more:
    https://github.com/chroma-core/chroma
    """

    def __init__(
            self, 
            configs: Dict[str, Any] = {},
            db_path: str = "/tmp/chromadb.db", 
            embedding_function: Optional[BaseEmbeddingFunction] = None,
            collection_name: Optional[str] = None,
    ) -> None:
        self.client = chromadb.Client(Settings(
            allow_reset=True,
            persist_directory=db_path,
            **configs
        ))
        self.configs = configs

        self.embedding_function = embedding_function
        self._collection_name = collection_name

        self.collection = self.client.get_or_create_collection(
            name = self.collection_name or "default_collection"
        )

        self.logger = get_logger(self.__class__.__name__)

    @property
    def db_path(self) -> str:
        return self.client.get_settings().persist_directory
    
    @db_path.setter
    def db_path(self, value: str) -> None:
        self.client = chromadb.Client(Settings(
            allow_reset=True,
            persist_directory=value,
            **self.configs
        ))

        self.collection = self.client.get_or_create_collection(
            name = self.collection_name or "default_collection"
        )

    @property
    def collection_name(self):
        return self._collection_name
    
    @collection_name.setter
    def collection_name(self, value):
        self._collection_name = value
        self.collection.modify(name=value)

    def add_data(
            self, 
            documents: List[str],
            ids: List[str],
            metadatas: Optional[List[Dict[str, Any]]] = None, 
            **optional_kwargs
    ) -> None:
        """
        Add data to the collection by creating embeddings for them.

        Args:
            documents (List[str]): List of documents to add.
            ids (List[str]): List of ids for the documents.
            metadatas (Optional[List[Dict[str, Any]]]): List of metadata for the documents.
            **optional_kwargs: Additional keyword arguments (see collection.add for more).
        """

        try:
            params = {
                "documents": documents,
                "ids": ids,
                **optional_kwargs
            }

            params["metadatas"] = metadatas or None
            
            # If an embedding function is provided, create embeddings for the documents
            if self.embedding_function:
                embeddings = self.embedding_function.create_embeddings(documents)
                params["embeddings"] = embeddings
            
            self.collection.add(**params)
        except Exception as e:
            self.logger.error(f"Error adding data to collection: {e}")
            raise e

    def query_data(
            self, 
            query_text: Optional[List[str]] = None,  
            query_embedding: Optional[List[List[float]]] = None,
            n_results: int = 10,
            **optional_kwargs
    ) -> QueryResult:
        """
        Query the collection for similar documents.

        Args:
            query_text (Optional[List[str]]): List of query texts.
            query_embedding (Optional[List[List[float]]]): List of query embeddings.
            n_results (int): Number of results to return.
            **optional_kwargs: Additional keyword arguments (see collection.query for more).

        Returns:
            QueryResult: The result of the query.
        """

        try:
            if query_text is None and query_embedding is None:
                raise ValueError("Either query_text or query_embedding must be provided.")
            
            params = {
                "n_results": n_results,
                **optional_kwargs
            }

            if query_text and query_embedding is None:
                if self.embedding_function:
                    query_embedding = self.embedding_function.create_embeddings(query_text)
                    params["query_embeddings"] = query_embedding
                else:
                    params["query_text"] = query_text

            elif query_embedding and query_text is None:
                params["query_embeddings"] = query_embedding

            elif query_embedding and query_text:
                params["query_embeddings"] = query_embedding
                
                if self.embedding_function:
                    embeddings = self.embedding_function.create_embeddings(query_text)
                    params["query_embeddings"] = query_embedding.extend(embeddings)
                else:
                    params["query_text"] = query_text

            return self.collection.query(**params)
        except Exception as e:
            self.logger.error(f"Error querying data from collection: {e}")
            raise e
        
    def query_by_id_or_metadata(
            self, 
            ids: Optional[List[str]] = None,
	        where: Optional[Where] = None,
            n_results: int = 10,
            **optional_kwargs
    ) -> GetResult:
        """
        Query the collection for similar documents.

        Args:
            ids (Optional[List[str]]): List of ids to query.
            where (Optional[Where]): Where clause to query.
            n_results (int): Number of results to return.
            **optional_kwargs: Additional keyword arguments (see collection.get for more).

        Returns:
            GetResult: The result of the query.
        """

        try:
            if ids is None and where is None:
                raise ValueError("Either ids or where must be provided.")
            
            params = {
                "n_results": n_results,
                **optional_kwargs
            }

            if ids:
                params["ids"] = ids
            if where:
                params["where"] = where

            return self.collection.get(**params)
        except Exception as e:
            self.logger.error(f"Error querying data from collection: {e}")
            raise e
        