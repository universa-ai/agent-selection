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
        system_prompt='You are an expert in vacation planning.',
        available_tools=["web_scraper"]  # we add the web_scraper tool to the agent
    )
    
    # Prompt the agent
    result = agent.invoke(
        'Get me the contents of this webpage: https://www.novakdjokovic.com/',
        auto_execute_tool=True
    )
    print(result)
    