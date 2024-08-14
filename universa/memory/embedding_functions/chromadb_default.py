from chromadb.utils import embedding_functions
from chromadb.api.types import Embeddings

from .base_embedder import BaseEmbeddingFunction
from ...utils._types import *
from ...utils.logs import get_logger


class ChromaDBDefaultEF(BaseEmbeddingFunction):
    """
    Default ChromadDB embedding function
    """
    def __init__(self):
        self.ef = embedding_functions.DefaultEmbeddingFunction()
        self.logger = get_logger(self.__class__.__name__)

    def create_embeddings(self, texts: List[str]) -> Embeddings:
        """
        Create embeddings for a list of texts.
        """
        try:
            return self.ef(texts) if self.ef is not None else []
        except Exception as e:
            self.logger.error(f"Error in creating embeddings: {e}")
            raise e
        