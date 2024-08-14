# Custom embeddings

You can use any embedding function of your choice to use it with our Vector Store classes. 
The process is very straightforward, and all you 
need to do is create a class that inherits from `BaseEmbeddingFunction` and add 
a method in it called `create_embeddings()`.

```python
class YourEmbeddingFunction(BaseEmbeddingFunction):
    """
    Description for your embedding function. 
    """

    def __init__(self, *args, **kwargs) -> None:
        """
        Initiate the class with all the necessary properties.
        """
        pass

    def create_embeddings(self, texts: List[str], *args, **kwargs) -> List[List[float]]:
        """
        Implementation of your create_embeddings() method.
        """
        pass
```

Following is a basic example to create a class for using OpenAI embedding function. 

```python
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
            base_url: str = os.environ["OPENROUTER_BASE_URL"],
            api_key: str = os.environ["OPENROUTER_API_KEY"],
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
```

To use this embedding function with our ChromaDB vector store class, you can 
follow the simple code below.

```python
import json
import uuid

from universa.memory.chromadb.chromadb import ChromaDB
from universa.memory.embedding_functions.your_embedding_function import OpenAIEmbeddingFn

ef = OpenAIEmbeddingFn(
    model_name="embedding function model",
    api_key="OpenAI API key",
    base_url="OpenAI Base Url",
)

chroma = ChromaDB(
    embedding_function=ef,
    collection_name="example_collection"
)

chroma.add_data(
    documents=[
        "Some random text about cars flying in the ocean",
        "Some random text about chickens coming home to roost", 
    ],
    ids=[str(uuid.uuid4()), str(uuid.uuid4())]
)

result = chroma.query_data(
    ["Do chickens give eggs?"], 
)

print(json.dumps({"results": result["documents"]}, indent=4))
```