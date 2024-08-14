from openai.types.chat import ChatCompletion

from .openai import OpenAI

from .schemas.openai import (
    OpenAIMessage,
    OpenAIInput,
    OpenAIOutput,
    OpenAIRequestError
)

from ..utils.execution import retry
from ..utils._types import *
from ..utils.logs import get_logger


class OpenRouterOpenAI(OpenAI):
    """
    Basic class for OpenRouter OpenAI client.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        input_schema: Optional[Type[OpenAIInput]] = None,
        output_schema: Optional[Type[OpenAIOutput]] = None,
        message_schema: Optional[Type[OpenAIMessage]] = None,
        **model_kwargs: Any
    ) -> None:
        """
        Initialize the API instance with the given base URL. If no API key is provided,
        it will be looked for in the environment variables.

        Args:
            base_url (str): Base URL for the API.
            api_key (str): API key for the given OpenAI protocol supporting API.
            model_name (Optional[str]): Model name for the API.
            input_schema (Optional[OpenAIInput]): Input schema for the API.
            output_schema (Optional[OpenAIOutput]): Output schema for the API.
            message_schema (Optional[OpenAIMessage]): Message schema for the API.
            model_kwargs (Any): Additional keyword arguments.
                To see a complete list of model arguments, see schemas.openai.OpenAIConstructor.
        """

        # Retrieve API & base URL
        self.api_key = api_key or self.retrieve_env_key(
            env_name=["OPENROUTER_API_KEY"]
        )
        # Retrieve API & base URL
        self.base_url = base_url or self.retrieve_env_key(
            env_name=["OPENROUTER_BASE_URL"]
        )

        super().__init__(
            base_url=self.base_url,
            api_key=self.api_key,
            model_name=model_name,
            input_schema=input_schema,
            output_schema=output_schema,
            message_schema=message_schema,
            **model_kwargs
        )

        self.logger = get_logger(self.__class__.__name__)

    def generate(
        self,
        messages: Union[List[OpenAIMessage], str],
        model: Optional[str] = None,
        return_type: Optional[Literal['choice', 'message', 'content', 'tool_calls']] = None,
        max_retries: int = 3,
        **input_kwargs,
    ) -> Union[ChatCompletion, str]:
        """
        Get the response from the API for a given prompt.

        Args:
            messages (Union[List[OpenAIMessage], str]): List of messages or a single message.
            model (Optional[str]): Model name to use.
            return_type (Optional[Literal['choice', 'message', 'content', 'tool_calls']]): Type of return.
            max_retries (int): Number of retries.
            input_kwargs (Any): Additional keyword arguments.
                For a complete list of input arguments, see schemas.openai.OpenAIInput.
        """
        # Create a proper message if it is just a string. 
        if isinstance(messages, str):
            messages = [self.create_message(role="user", content=messages)]

        # Process tools related arguments
        tools = input_kwargs.get("tools", None)
        tool_choice = input_kwargs.get("tool_choice", None)
        input_kwargs.update(
            messages=messages,
            model=model or self.model_name,
            tool_choice=tool_choice if tools else None,
        )

        # Validate inputs
        validated_input = self.input_schema.validate(
            args_to_validate=input_kwargs,
            to_dict=True,
        )

        # Get the response through the API
        create = retry(num_retries=max_retries)(
            self.client.chat.completions.create
        )
        response = create(
            **validated_input
        )

        error = getattr(response, "error", None)
        if error:
            raise OpenAIRequestError("OpenRouter model failed to generate response"
                                     f" and raised the following error: {error}")

        # Parse and return the response
        if return_type:
            return self.parse_response(response, return_type)
        
        return response
    