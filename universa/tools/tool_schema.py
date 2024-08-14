from typing import Any, Dict

from pydantic import Field

from ..schema import Schema
from ..utils.logs import get_logger
from ..utils.registry import generate_id


logger = get_logger(__name__)

class ToolCall(Schema):
    """
    Tool call message schema.
    """
    function_name: str = Field(description="Name of the function that has will be executed.")
    function_params: Dict[str, Any] = Field(description="Parameters with which the function will be executed.")
    additional_info: Dict[str, Any] = Field(description="Additional information about the tool call.")

    def get_tool_call_id(self) -> str:
        """
        Get the tool call ID.
        """
        id = self.additional_info.get("id", None)
        if id is None:
            logger.warning("Tool call ID not found in the tool call message. Using custom id.")
            id = generate_id()

        return id

class ToolCallResult(Schema):
    """
    Tool call result schema.
    """
    function_name: str = Field(description="Name of the function that was executed.")
    result: Any = Field(description="Result of the tool call.")
