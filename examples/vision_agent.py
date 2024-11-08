import _import_root  # noqa : E402

from PIL import Image

from universa.agents import BaseAgent
from universa.models.vision import OpenAIVision


if __name__ == "__main__":
    
    # Create OpenRouter OpenAI connection
    openai = OpenAIVision(
        model_name='openai/gpt-4o-mini',
        max_retries=1,
        base_url='https://openrouter.ai/api/v1'
    )

    # Create a new agent
    agent = BaseAgent(
        name='Personal Assistant',
        model=openai,
        description='A personal assistant agent.',
        system_prompt='You are an image analyser.'
    )
    
    # Prompt the agent using a web image
    query = openai.create_query(
        inquiry='What is in this image?',
        images=["https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTW024VNDwxZ-37LljCNePXQ5ANzBO5FJIKAoKmv7tNAA&s"],
        image_qualities=["low"]
    )
    result = agent.invoke(
        query,
        max_tokens=100
    )
    print(result)

    # Prompt the agent using a local image
    image = Image.open("/Users/neurowelt/Desktop/beluga.png")
    query = openai.create_query(
        inquiry='What is in this image?',
        images=[image],
        image_qualities=["low"]
    )
    result = agent.invoke(
        query,
        max_tokens=100
    )
    print(result)
    