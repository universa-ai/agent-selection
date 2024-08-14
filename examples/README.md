# Universa Examples

In this directory you will find a handful of simple examples that demonstrate things you can do with Universa AI agents & tools.

You will find the following scripts in this directory:
* [Simple agent creation](./agent_creation.py)
* [Agent tool calling](./tool_calling.py)
* [Using a vector store](./vector_store.py)
* [Using vision agent](./vision_agent.py)

You can also find code used to calculate case studies in the [case_study.py](./case_study.py) file.

Note that in our examples we are using an OpenRouter class based on OpenAI class. You can easily replace the creation of the OpenRouter class with OpenAI class simply with this method:

```python
from universa.models.openai import OpenAI

openai = OpenAI(model_name='gpt-4-turbo', api_key='your_api_key', base_url='https://api.openai.com/v1')
```

In case of using different models in your everyday work, please do not hesitate to contact us at [challenge@universa.org](mailto:challenge@universa.org) - we will be happy to help you with any modifications that will help you with the challenge.
