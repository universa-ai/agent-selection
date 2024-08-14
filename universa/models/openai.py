import json

from openai import OpenAI as OpenAIClient
from openai.types.chat import ChatCompletion

from ..agents.chat import (
    ChatHistory
)

from .model import (
    ToolCaller,
    AvailableTools
)

from ..tools import (
    BaseTool,
    ToolRegistry,
    ToolCall,
    ToolCallResult,
    JsonSchemaValue
)

from ..schema import Schema
from .schemas.openai import (
    OpenAIMessage,
    OpenAIOutputMessage,
    OpenAIInput,
    OpenAIOutput,
    OpenAIToolCallMessage,
    OpenAIConstructor,
    OpenAIRequestError,
    OpenAIResponse
)

from ..utils.execution import retry
from ..utils._types import *
from ..utils.imports import (
    import_specific_modules,
    import_modules_from_directory,
)


class OpenAI(ToolCaller):
    """
    Basic class for OpenAI client.
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
            env_name=["OPENAI_API_KEY", "API_KEY"]
        )
        self.base_url = base_url
        self.model_kwargs = model_kwargs
        
        constructor_kwargs = {**model_kwargs}
        constructor_kwargs.update(
            api_key=self.api_key,
            base_url=self.base_url
        )

        constructor = OpenAIConstructor.validate(
            args_to_validate=constructor_kwargs,
            to_dict=True
        )

        # Initialize the OpenAI client, register
        self.client = OpenAIClient(
            **constructor
        )
        self.register()
        self.model_name = model_name

        # Create OpenAI schemas
        self.message_schema = message_schema or OpenAIMessage
        self.input_schema = input_schema or OpenAIInput
        self.output_schema = output_schema or OpenAIOutput

        # Create tool calling config
        self.tool_registry = None
        self.tools = None
        self.tool_choice = None

    def set_model(self, model_name: str) -> None:
        """
        Set up the model used by the API.

        Args:
            model_name (str): Model name for the API to use.
        """
        if self.model_name:
            self.logger.info(f"Changed model for `{self.model_name}` to `{model_name}`.")
        self.model_name = model_name

    def create_message(self, role: str, content: Union[str, Schema]) -> OpenAIMessage:
        """
        Create a message for the OpenAI API.

        Args:
            role (str): Role of the message.
            content (str): Content of the message.

        Returns:
            OpenAIMessage: Message dictionary with role and content.
        """
        if isinstance(content, str):
            return self.message_schema.validate(
                dict(role=role, content=content),
                to_dict=False
            )

        if isinstance(content, Schema):
            content = json.dumps(content.dict())
            return self.message_schema.validate(
                dict(role=role, content=content),
                to_dict=False
            )
    
    def parse_response(
        self,
        response: ChatCompletion,
        parsing_type: Literal['choices', 'message', 'content', 'tool_calls'] = 'content',
    ) -> Any:
        """
        Parse the response from the OpenAI API. If no type is specified, simply returns
        the response.

        Args:
            response (Any): Response to parse.
            parsing_type (Optional[str]): Type of parsing to use.

        Returns:
            Any: Parsed response.
        """
        if response.choices:
            if parsing_type == "choices":
                return response.choices
            elif parsing_type == "message":
                return response.choices[0].message
            elif parsing_type == "content":
                return response.choices[0].message.content
            elif parsing_type == "tool_calls":
                return response.choices[0].message.tool_calls
        return response
    
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
        # TODO: Cannot possibly keep retry like that. Has to be for the whole generate() method.
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
    
    def update_tool_configs(
        self, 
        model_kwargs: Dict[str, Any], 
        mode: Literal["add", "remove"] = "add"
    ) -> None:
        """
        Update the tool configurations for the Model. These configs are different for each model 
        and will be used to invoke the model for tool use.
        
        For OpenAI, the parameters for tool calling is 'tools' and 'tool_choice'.
        """
        # Get existing tool configs
        tools = model_kwargs.get("tools", None)
        tool_choice = model_kwargs.get("tool_choice", None)

        # Update the tool configs based on the mode
        if mode == "add" and tools:
            return
        
        if mode == "add" and tools is None:
            if self.tools is None:
                return
            else:
                model_kwargs.update(
                    tools=self.tools, 
                    tool_choice=tool_choice or "auto"
                )

        elif mode == "remove" and tools:
            model_kwargs.update(
                tools=None, 
                tool_choice=None
            )
    
    def _prepare_all_tools(self) -> None:
        """
        Prepare all registered tools for the agent.

        This method imports modules from a certain directory and initializes the tool registry instance
        from the imported tools. It also sets the tools as schema and the tool choice as "auto".

        Returns:
            None
        """
        try:
            tool_addresses = import_modules_from_directory(
                "universa/tools/extensions"
            )
        except ModuleNotFoundError as e:
            e.msg += "\nAll the tool modules must be inside the 'universa/tools/extensions' directory."
            raise e

        # Initiate the tool registry instance from all tools
        self.tool_registry = ToolRegistry.from_tool_names(tool_names=tool_addresses)
        self.tools = self.tool_registry.get_tools_as_schema(func=self.get_function_schema)
        self.tool_choice = "auto"

    def _prepare_specific_tools(self, available_tools: List[str]) -> None:
        """
        Prepare specific tools based on the given list of available tools for the agent.

        Args:
            available_tools (List[str]): A list of tool names.

        Returns:
            None
        """
        tool_addresses = [
            f"universa.tools.extensions.{tool_name}" for tool_name in available_tools
        ]
        try:
            import_specific_modules(tool_addresses)
        except ModuleNotFoundError as e:
            e.msg += "\nAll the tool modules must be inside the universa/tools/extensions directory."
            raise e

        # Initiate the tool registry instance from the mentioned tools
        self.tool_registry = ToolRegistry.from_tool_names(tool_names=tool_addresses)
        self.tools = self.tool_registry.get_tools_as_schema(func=self.get_function_schema)
        self.tool_choice = "auto"

    def prepare_tools(self, available_tools: AvailableTools = None) -> None:
        """
        Prepare the tools for the agent.
        """
        if available_tools == "all":
            # Register all the tools available in the extensions directory
            self._prepare_all_tools()

        elif isinstance(available_tools, list):
            # Register only the mentioned tools
            self._prepare_specific_tools(available_tools=available_tools)

        elif available_tools is None:
            # This agent is not a tool calling agent.
            self.tool_registry = None
            self.tools = None
            self.tool_choice = None
        
        else:
            raise ValueError(
                "Invalid value for `available_tools`."
                " It can be either 'all' or a list of tool names."
                " This value can be omitted if the agent is not using any tools."
            )
        
    def use_response_format(
            self, 
            model_kwargs: Dict[str, Any],
            schema: Optional[Type[OpenAIOutput]] = None
    ) -> None:
        """
        Use response format for the model.
        """
        if schema is None:
            return
        model_kwargs.update(response_format={
            "type": "json_object",
        })
    
    def handle_tool_calls(
            self,
            *,
            response: ChatCompletion,
            chat_history: ChatHistory,
            model_kwargs: Any,
            auto_execute_tool: bool,
            memory_window: Optional[int] = None,
    ) -> Optional[Union[OpenAIResponse, List[ToolCall]]]:
        """
        Handle response in order to extract and execute tool call.
        """
        # Return None if tool call is not made
        tool_call_infos = self.get_tool_call_info(response)
        if tool_call_infos is None:
            return

        # Execute the tool and get chat response based on the result of the tool call
        response_message = response.choices[0].message
        tool_response_instance = OpenAIOutputMessage(**response_message.model_dump())
        chat_history.messages.append(tool_response_instance)

        # Exit here if auto_execute_tool is False
        if not auto_execute_tool:
            return tool_call_infos
        
        # Execute the tool
        execution_results = BaseTool.execute_tool(tool_call_infos, self.tool_registry)
        tool_call_messages = self.create_tool_call_messages(
            tool_call_infos=tool_call_infos,
            tool_call_results=execution_results
        )

        # Save the tool call messages to the chat history
        for msg in tool_call_messages:
            chat_history.save_message(msg)

        # Update tool calling configs
        self.update_tool_configs(model_kwargs, mode="remove")

        # Re-invoke the models
        return self.generate(
            messages=chat_history.get_history(memory_window=memory_window)[0],
            model=self.model_name,
            **model_kwargs,
        )
    
    @staticmethod
    def get_tool_call_info(response: ChatCompletion) -> Union[None, List[ToolCall]]:
        """
        Get the tool call information from the output of OpenAI response.
        """
        tool_calls = response.choices[0].message.tool_calls
        if tool_calls is None:
            return None
        
        # If tool call is made, return the function name and arguments of all tool calls.
        tool_call_infos = []
        for tool_call in tool_calls:
            func_name = tool_call.function.name
            func_params = json.loads(tool_call.function.arguments)
            additional_info = {
                "id": tool_call.id,
                "type": tool_call.type
            }
            tool_call_infos.append(
                ToolCall(
                    function_name=func_name,
                    function_params=func_params,
                    additional_info=additional_info
                )
            )
        
        return tool_call_infos

    @staticmethod
    def create_tool_call_messages(
            tool_call_infos: List[ToolCall],
            tool_call_results: Dict[str, ToolCallResult]
    ) -> List[OpenAIToolCallMessage]:
        """
        Get the OpenAI messages from the tool call results that will be appended later on. 
        """
        tool_call_messages = []
        for info in tool_call_infos:
            tool_call_id = info.get_tool_call_id()
            execution_result = tool_call_results[tool_call_id]
            tool_call_message = OpenAIToolCallMessage.validate(
                {
                    "tool_call_id": tool_call_id,
                    "role": "tool",
                    "name": execution_result.function_name,
                    "content": execution_result.result
                },
                to_dict=False
            )

            tool_call_messages.append(tool_call_message)

        return tool_call_messages
    
    @staticmethod
    def add_tool_response(
        response: ChatCompletion,
        chat_history: ChatHistory
    ) -> None:
        """
        Adds the first tool call response to the chat history. This is specific to only OpenAI models. 
        Also, this method is basically the first couple of lines from the method `handle_tool_call()`
        """
        response_message = response.choices[0].message
        tool_response_instance = OpenAIOutputMessage(**response_message.model_dump())
        chat_history.messages.append(tool_response_instance)
    
    @staticmethod
    def get_function_schema(tool: BaseTool) -> JsonSchemaValue:
        """
        Creates the JSON schema representation of the function, the type of format required by OpenAI and its variants.

        Returns:
            JsonSchemaValue: The JSON schema representation of the function.

        Examples:

        ```python
        def f(a: Annotated[str, "Parameter a"], b: int = 2, c: Annotated[float, "Parameter c"] = 0.1) -> None:
            pass

        base_tool = BaseTool.from_function(f, description="function f")
        schema = OpenAI.get_function_schema(base_tool)

        {
            "type": "function",
            "function": {
                "description": "function f",
                "name": "f",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "a": {"type": "str", "description": "Parameter a"},
                        "b": {"type": "int", "description": "b"},
                        "c": {"type": "float", "description": "Parameter c"},
                    },
                    "required": ["a"],
                },
            },
        }
        ```
        """
        function_json_schema = {
            "type": "function",
            "function": {
                "description": tool.description,
                "name": tool.name,
                "parameters": tool.input_schema.to_schema(),
            },
        }

        return function_json_schema
    