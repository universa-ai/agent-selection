import json
import os
import re
import time

from ..models.model import (
    ToolCaller, 
    AvailableTools
)
from ..models.openai import (
    ChatCompletion,
    OpenAI
)
from ..models.message import BaseMessage
from .chat import ChatHistory, Metadata

from ..core import (
    Executable,
    SerializedType,
    DeserializableType
)
from ..schema import Schema
from ..tools import ToolCall

from ..utils._types import Any, Optional, Dict, Union, Self
from ..utils.imports import get_parent_path
from ..utils.execution import request_user_input


class BaseAgent(Executable):
    """
    Base class for creating Autonomous AI Agents.

    Args:
        name (str, optional): The name of the agent. Defaults to "Assistant".
        description (str, optional): A short description of the agent.
        system_prompt (str, optional): The system prompt that will dictate the behavior and role of the agent.
        model (ToolCaller, optional): The base model for the agent used for generating responses.
            If `None` is passed then OpenAI class is created automatically.
        available_tools (AvailableTools, optional): The available tools for the agent.
                        It can be either "all" if the agent is given all the registered tools to use.
                        Or it can be a list of tool names if the agent is able to use only certain tools from all the registered tools.
                        If this value is not given, then the agent will not use any tool calls in its response.
                        Defaults to None.
        max_retries (int, optional): The maximum number of retries for invoking the agent. Defaults to 1.
        auto_reinvoke (bool, optional): Whether to automatically re-invoke the agent
            if the response is not in the proper json format. Defaults to True.
        memory_window (int, optional): The size of the agent's memory window. A size of 5 means that the last 5 messages
            from the chat history will be used as memory for the agent. Defaults to 5.
        extraction_boundary (Dict[str, str], optional): The extraction boundary for extracting the output from the response.
    """

    def __init__(
        self,
        name: str = "Assistant",
        description: str = "An Autonomous AI Agent to solve problems.",
        system_prompt: str = "You are a helpful AI assistant.",
        model: Optional[ToolCaller] = None,
        available_tools: Optional[AvailableTools] = None,
        max_retries: int = 1,
        auto_reinvoke: bool = True,
        memory_window: int = 5,
        extraction_boundary: Optional[Dict[str, str]] = None,
        object_id: Optional[str] = None
    ) -> None:
        
        # Basic agent information
        self.name = name
        self.description = description
        self.system_prompt = system_prompt
        self.register(object_id=object_id)  # create ID & logger

        # Model & tools
        self.model: ToolCaller = model or OpenAI.from_json(
            os.path.join(get_parent_path(__file__, 2), 'models/schemas/openai.json')
        )
        self.available_tools = available_tools
        self.model.prepare_tools(available_tools=available_tools)

        # Core schemas
        self.output_schema = None
        self.message_schema = self.model.message_schema

        # Chat history
        self.chat_history = ChatHistory(message_schema=self.message_schema)
        self.memory_window = memory_window  # how many messages back in history to look at when querying
        self._create_and_save_message(role="system", content=self.system_prompt)  # save the initial system prompt
        
        # Invoke retry & extraction parameters
        self.max_retries = max_retries
        self.auto_reinvoke = auto_reinvoke
        self.extraction_boundary = extraction_boundary or {
            "start": "```json",
            "end": """```"""
        }

        # Avergae response time
        self.response_time: float = 0.0

        # Response cost of the agent (per 1M in $ tokens)
        self.input_cost: float = 0.0
        self.output_cost: float = 0.0

        # Agent popularity (how often it is used)
        self.popularity: int = 0

        # Agent average response ratings
        self.rated_responses: int = 0
        self.average_rating: float = 0.0

    def _create_and_save_message(
            self, 
            role: str, 
            content: Any,
            is_end_conv: bool = False,
            metadata: Optional[Metadata] = None
    ) -> None:
        """
        Create a message and save it to the chat history.
        """
        if metadata and "rating" in metadata:
            self.rated_responses += 1
            self.average_rating = ((self.average_rating * (self.rated_responses - 1)) + metadata["rating"]) / self.rated_responses
        message = self.model.create_message(role=role, content=content)
        self.chat_history.save_message(message, is_end_conv=is_end_conv, metadata=metadata)

    def _extract_from_string(self, content: str) -> Optional[str]:
        """
        Uses regex and string methods to extract the necessary texts.
        """
        start = self.extraction_boundary['start']
        end = self.extraction_boundary['end']

        result = re.search(rf"{start}(.*){end}", content, flags=re.DOTALL)

        if result:
            return result.group(1).strip()
        else:
            result = re.search(r"[{].*[}]", content, flags=re.DOTALL)
            return result.group().strip() if result else None

    def _extract_json_output(self, content: str, model_kwargs: Any) -> Dict[str, Any]:
        """
        Extract JSON output from the response. 
        If the response is not in JSON format, it tries to extract it using regex.
        """
        is_invalid = False
        error_message = ""

        # Iterate until we extract or hit max retries
        for i in range(self.max_retries):

            # Use regex to extract content from the response.
            extracted_content = self._extract_from_string(content=content)

            if extracted_content is not None:
                try:
                    parsed_string = json.loads(extracted_content)
                except Exception as e:
                    error_message = str(e)
                    is_invalid = True

                if not is_invalid:
                    try:
                        # Validate the extracted content
                        return self.output_schema.validate(
                            args_to_validate=parsed_string,
                            to_dict=False
                        )
                    except Exception as e:
                        is_invalid = True
                        error_message = str(e)
            
            if is_invalid or extracted_content is None:
                if i != self.max_retries - 1 and self.auto_reinvoke:
                    self.logger.error("Output was not given in proper json format. Re-invoking the agent.") 
                    self._create_and_save_message(
                        role="user", 
                        content=" ".join([
                            "Your response is not in the proper json format.",
                            "Please provide the response in the format that you are instructed to.",
                            "The following error occurred while parsing the JSON response:\n",
                            error_message
                        ])
                    )

                    # Update tool calling config
                    self.model.update_tool_configs(model_kwargs, mode="remove")

                    # Re-invoke
                    reinvoke_result = self.model.generate(
                        messages=self.chat_history.get_history(memory_window=self.memory_window),
                        model=self.model.model_name,
                        **model_kwargs,
                    )

                    content = self.model.parse_response(response=reinvoke_result, parsing_type="content")
                    continue
                else:
                    self.logger.warning("Output could not be extracted into proper json format. Returning the output as it is.")
                    return extracted_content
                
    def invoke(
        self,
        query: Any,
        auto_execute_tool: bool = True,
        ask_for_feedback: bool = False,
        **model_kwargs: Any
    ) -> Union[ChatCompletion, str, ToolCall, Schema]:
        """
        Invoke the agent with a query. 

        Args:
            query (Any): The query for the agent.
                Most of the time, the query will be a string. But it can be of any type.  
            auto_execute_tool (bool): Whether to automatically execute tools available to the agent.
            ask_for_feedback (bool): Whether to ask for feedback from the user.
            model_kwargs (Any): Additional keyword arguments.
                To see available model input arguments, see given model's input schema (agent.model.input_schema).

        Returns:
            Union[ChatCompletion, str, ToolCall, Schema]: The response from the agent.
        """
        # Start the clock
        t0 = time.perf_counter()

        # Update chat history
        self._create_and_save_message(role="user", content=query)

        # Update tool configs
        self.model.update_tool_configs(model_kwargs, mode="add")

        # Get response format argument
        if hasattr(self.model, 'use_response_format'):
            self.model.use_response_format(
                model_kwargs=model_kwargs, 
                schema=None
            )
        
        # Generate model response
        system_message = self.chat_history.messages[0]
        messages = self.chat_history.get_history(memory_window=self.memory_window-1)[0]
        response = self.model.generate(
            messages=[system_message] + messages,
            model=getattr(self.model, "model_name", None),
            **model_kwargs,
        )

        # Handle tool calls
        if issubclass(self.model.__class__, ToolCaller):
            result = self.model.handle_tool_calls(
                response=response,
                chat_history=self.chat_history,
                model_kwargs=model_kwargs,
                auto_execute_tool=auto_execute_tool,
                memory_window=self.memory_window
            )

            if result is not None:
                if isinstance(result, list):
                    return result
                else:
                    response = result
                    
        # Parse & validate the response
        content = self.model.parse_response(response=response, parsing_type="content")
        
        if self.output_schema:
            content = self._extract_json_output(content=content, model_kwargs=model_kwargs)

        # Update system parameters
        t1 = time.perf_counter()
        self.popularity += 1
        self.response_time = ((self.response_time * self.popularity) + (t1 - t0)) / self.popularity

        if ask_for_feedback:
            self.logger.info(f"Asking for feedback from the user for the following response:\n\n{content}\n")
            rating = request_user_input(
                "Please rate the response with a numerical value between 1 and 10",
                response_type=int,
                ranges=(1, 10)
            )
            self.logger.info(f"User rated the response with a value of {rating} - saving for the given result.")
            self._create_and_save_message(role="assistant", content=content, metadata={"rating": rating})
        else:
            self._create_and_save_message(role="assistant", content=content)

        return content
    
    def get_latest_response(self) -> BaseMessage:
        """
        Gets the latest message from the chat history.
        """
        return self.chat_history.messages[-1]

    def to_json(self, save_path: str | None = None, exist_ok: bool = False, add_chat_history: bool = False) -> SerializedType:
        """
        Override executable `to_json` method to include additional agent information.
        """
        _serialized = super().to_json()
        _serialized.update({
            "response_time": self.response_time,
            "input_cost": self.input_cost,
            "output_cost": self.output_cost,
            "popularity": self.popularity,
            "rated_responses": self.rated_responses,
            "average_rating": self.average_rating,
        })
        if add_chat_history:
            _serialized["chat_history"] = self.chat_history.serialize()

        if save_path:
            self.save_json(
                data=_serialized,
                path=save_path,
                exist_ok=exist_ok
            )

        return _serialized
    
    @classmethod
    def from_json(cls, serialized: DeserializableType, model: Optional[ToolCaller] = None) -> Self:
        """
        Override executable `from_json` method to allow for model passing when loading an agent.
        """
        constructor_args = super().from_json(serialized, only_args=True)
        constructor_args["model"] = model

        # Extract agent parameters that are not constructor arguments
        response_time = constructor_args.pop("response_time")
        input_cost = constructor_args.pop("input_cost")
        output_cost = constructor_args.pop("output_cost")
        popularity = constructor_args.pop("popularity")
        rated_responses = constructor_args.pop("rated_responses")
        average_rating = constructor_args.pop("average_rating")
        chat_history = constructor_args.pop("chat_history", None)
        instance = cls(**constructor_args)

        # Update agent parameters
        instance.response_time = response_time
        instance.input_cost = input_cost
        instance.output_cost = output_cost
        instance.popularity = popularity
        instance.rated_responses = rated_responses
        instance.average_rating = average_rating
        
        # Remove first system message from the chat history
        if chat_history is not None and chat_history[0]["message"]["role"] == "system":
            chat_history.pop(0)

            # Deserialize chat history
            chat_history = ChatHistory.deserialize(
                chat_history,
                message_schema=instance.message_schema
            )
            for message, metadata in zip(chat_history.messages, chat_history.metadata):
                instance.chat_history.save_message(
                    message, 
                    metadata=metadata
                )

        return instance
    