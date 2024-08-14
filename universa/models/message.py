import time

from ..schema import Schema
from ..utils.registry import generate_id


class BaseMessage(Schema):
    """
    Base message object implemented by all message types.
    """
    def __init__(self, *args, **kwargs) -> None:
        """
        Initialize the base message.
        """

        super().__init__(*args, **kwargs)

    def __repr__(self) -> str:
        """
        Create base representation of the message.
        """
        _cls_name = self.__class__.__name__
        _cls_attrs = str(vars(self))
        return f"{_cls_name}({_cls_attrs})"
    
    def __str__(self) -> str:
        """
        Create string representation of the message.
        """
        msg = [f"{self._format_string(k)}: {v}" for k, v in vars(self).items()]
        return "\n".join(msg)
    
    def to_dict(self) -> dict:
        """
        Convert the message to a dictionary.
        """
        return vars(self)
    
    def _format_string(self, v: str) -> str:
        """
        Helper method to parse key-like names to readable format.
        """
        return v.replace("_", " ").title()

    @staticmethod
    def create_timestamp() -> int:
        return int(time.time())
    
    @staticmethod
    def create_id() -> str:
        return generate_id()
    