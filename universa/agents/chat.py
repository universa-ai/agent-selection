from copy import deepcopy

from ..models.message import BaseMessage

from ..utils._types import *


Metadata = Dict[str, Any]

class ChatHistory:
    """
    Chat History should contain the schema of the message and the messages themselves.
    """
    def __init__(
        self, 
        messages: Optional[List[BaseMessage]] = None,
        metadata: Optional[List[Metadata]] = None,
        message_schema: Optional[Type[BaseMessage]] = None,
    ) -> None:
        if (metadata and messages) and (len(messages) != len(metadata)):
            raise ValueError("Length of messages and metadata should be equal.")
        self.messages = messages if messages else []
        self.metadata = metadata if metadata else [{} for _ in range(len(self.messages))]
        self.message_schema = message_schema
        self.conv_chunks: List[int] = []

    def get_history(
            self, memory_window: Optional[int] = None, include_metadata: bool = False
    ) -> Tuple[List[BaseMessage], Optional[List[Metadata]]]:
        """
        Get the chat history.
        """
        if memory_window and len(self.conv_chunks) > memory_window:

            new_conv_chunks = self.conv_chunks[-memory_window:]
            old_conv_chunks = self.conv_chunks[:-memory_window]

            # Adjust the indexes of the new conversation chunk after the slicing.
            index_adjustment = 0
            for i in old_conv_chunks:
                index_adjustment += i

            sys_prompt = self.get_system_prompt()
            if sys_prompt:
                self.conv_chunks = [1, *new_conv_chunks]
                return (
                    [sys_prompt, *self.messages[new_conv_chunks[0]:]],
                    [{}, *self.metadata[new_conv_chunks[0]:]] if include_metadata else None
                )
            else:
                self.conv_chunk = [index - index_adjustment for index in new_conv_chunks]
                return (
                    self.messages[new_conv_chunks[0]:],
                    self.metadata[new_conv_chunks[0]:] if include_metadata else None
                )

        return (
            self.messages, self.metadata if include_metadata else None
        )
    
    def get_system_prompt(self) -> Optional[BaseMessage]:
        """
        Get the system prompt from the chat history.
        """
        system_message = deepcopy(self.messages[0])
        return system_message if system_message.role == "system" else None
    
    def update_history(self, new_messages: List[BaseMessage]) -> List[BaseMessage]:
        """
        Update the chat history with new messages.
        """
        self.messages = new_messages
        return new_messages
    
    def save_message(
            self,
            message: Union[BaseMessage, List[BaseMessage]],
            is_end_conv: bool = False,
            metadata: Optional[Metadata] = None
    ) -> List[BaseMessage]:
        """
        Append message to the chat history.
        """
        if isinstance(message, BaseMessage):
            self.messages.append(message)
            if message.role == "system" or message.role == "assistant" or is_end_conv:
                self.conv_chunks.append(len(self.messages))

        elif isinstance(message, list):
            for msg in message:
                if not isinstance(msg, BaseMessage):
                    raise TypeError("Message should be of type BaseMessage or a list of BaseMessage.")
                self.messages.append(message)
                if message.role == "system" or message.role == "assistant":
                    self.conv_chunks.append(len(self.messages))

        self.metadata.append(
            metadata if metadata else {}
        )

        return self.messages
    
    def get_recent_message(self):
        """
        Get the most recent message from the chat history.
        """
        return self.messages[-1]

    def clear_history(self) -> None:
        """
        Clear the chat history.
        """
        self.messages = []
        self.conv_chunks = []

    def serialize(self) -> List[Dict[str, Any]]:
        """
        Serialzie the history to JSON format.
        """
        return [
            {
                "message": message.to_dict(),
                "metadata": metadata
            } for message, metadata in zip(self.messages, self.metadata)
        ]
        
    @classmethod
    def deserialize(cls, serialized: List[Dict[str, Any]], message_schema: BaseMessage) -> Self:
        """
        Deserialize the history from JSON format.
        """
        instance = cls()
        for item in serialized:
            message, metadata = item["message"], item["metadata"]
            instance.save_message(
                message=message_schema.validate(
                    args_to_validate=message,
                    to_dict=False
                ),
                metadata=metadata
            )
        
        return instance
    