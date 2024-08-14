from abc import abstractmethod

from ..core import Executable

from ..schema import Schema
from .message import BaseMessage

from ..tools import BaseTool

from ..utils.logs import general_logger
from ..utils._types import *

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    general_logger.info(
        "dotenv is not installed - if you're using API, loading keys from .env is recommended!"
    )

AvailableTools = Optional[Union[Literal["all"], List[str]]]


class CoreModel(Executable):
    """
    Abstract representation of all models.

    All models inheriting from this class are required to implement the following methods:
    * `generate` - create response/output from the model or API
    * `parse_response` - apply processing of the model response
    * `create_message` - create a message for the model
    """
    message_schema: Schema

    @property
    def response_format(self) -> str:
        """
        Return the response format of the model.
        """
        pass

    @abstractmethod
    def parse_response(self, response: Any, parsing_type: str) -> Any:
        """
        Parse the response from the model based on a certain type.
        """
        pass

    @abstractmethod
    def create_message(self, **input_kwargs) -> BaseMessage:
        """
        Create a message for the model based on its accepted structure.
        """
        pass
        
    @abstractmethod
    def generate(self, messages: List[Schema], **kwargs) -> Any:
        """
        Generate output from the model.
        """
        pass
    
class ToolCaller(CoreModel):
    """
    Basic interface for models with tool calling ability.
    """
    @abstractmethod
    def prepare_tools(self, available_tools: Optional[AvailableTools] = None) -> List[Any]:
        """
        Prepare the tools for the API.
        """
        pass
    
    @abstractmethod
    def update_tool_configs(self, model_kwargs: Dict[str, Any], is_adding: bool) -> None:
        """
        Update the tool call configuration for the model.
        """
        pass

    @abstractmethod
    def handle_tool_calls(self, response: Any, **kwargs) -> Any:
        """
        Handle the tool calls from the response.
        """
        pass

    @staticmethod
    @abstractmethod
    def get_tool_call_info(response: Any) -> Any:
        """
        Get the tool call information from the response.
        """
        pass

    @staticmethod
    @abstractmethod
    def create_tool_call_messages(response: Any, tool_call_result: Any) -> List[BaseMessage]:
        """
        Create tool call messages from the tool call result.
        """
        pass

    @staticmethod
    @abstractmethod
    def get_function_schema(tool: BaseTool) -> JsonSchemaValue:
        """
        Get the schema for the tool function.
        """
        pass
