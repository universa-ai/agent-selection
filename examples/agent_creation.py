import _import_root  # noqa : E402
from universa.agents import BaseAgent
from universa.models.openrouter import OpenRouterOpenAI


if __name__ == "__main__":
    
    # Create OpenRouter OpenAI connection
    openai = OpenRouterOpenAI(
        model_name='openai/gpt-4o',
        max_retries=1
    )

    # Create a new agent
    agent = BaseAgent(
        name='Personal Assistant',
        model=openai,
        description='A personal assistant agent.',
        system_prompt='You are an expert in vacation planning.'
    )
    
    # Prompt the agent
    result = agent.invoke(
        'What is the best place to visit in the summer?',
        max_tokens=100
    )
    print(result)
    
    # You can also save this agent to a JSON file
    agent.to_json(
        save_path='agent.json',
        exist_ok=True
    )

    # And load it back passing the same model you used
    agent = BaseAgent.from_json(
        serialized='agent.json',
        model=openai
    )
    