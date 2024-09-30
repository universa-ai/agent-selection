# Algorithm Testing

In this directory you will find multiple agent examples with different descriptions and parameters on which you can test your selection algorithms, get to know the repository and start building your solution.

Each agent is presented in a JSON format which can be loaded into an agent object via a simple class method:

```python
from universa.agents import BaseAgent

# Create OpenRouter OpenAI connection
openai = OpenRouterOpenAI(
    model_name='openai/gpt-4o',
    max_retries=1
)

# Load agent from JSON
agent = BaseAgent.from_json(
    serialized='testing/agents/ai-engineer.json',
    model=openai
)
```
