import os

from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

from .base_embedder import BaseEmbeddingFunction
from ...utils._types import *


class OpenAIEmbeddingFn(BaseEmbeddingFunction):
    """
    An embedding function that uses OpenAI's GPT models to embed data.
    """
    def __init__(
            self, 
            model_name: str = "text-embedding-3-small",
            base_url: str = os.environ["OPENAI_BASE_URL"],
            api_key: str = os.environ["OPENAI_API_KEY"],
            **configs
    ) -> None:
        self.model_name = model_name
        self.base_url = base_url
        self.api_key = api_key

        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key
        )

    def create_embeddings(self, data: str, *args, **kwargs) -> List[float]:
        response = self.client.embeddings.create(
            input=data,
            model=self.model_name
        )
    
        return response.data[0].embedding
