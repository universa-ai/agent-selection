import sys
from typing import TYPE_CHECKING

from .utils.imports import LazyModule


_import_structure = {
    "agents": {
        "agent": ["BaseAgent"],
        "chat": ["ChatHistory"]
    },
    "engine": {
        "schema": ["Schema"],
    },
    "models": {
        "openai": ["OpenAI"],
        "openrouter": ["OpenRouterOpenAI"],
        "model": ["CoreModel", "ToolCaller"],
        "message": ["BaseMessage"]
    },
    "tools": {
        "tool": ["BaseTool", "ToolRegistry"]
    }
}


if TYPE_CHECKING:
    
    # Agents
    from .agents.agent import BaseAgent
    from .agents.chat import ChatHistory

    # Models
    from .models.model import CoreModel, ToolCaller
    from .models.openai import OpenAI
    from .models.openrouter import OpenRouterOpenAI

    # Engine
    from .schema import Schema

    # Protocol
    from .models.message import BaseMessage

    # Tools
    from .tools.tool import BaseTool, ToolRegistry

else:
    
    sys.modules[__name__] = LazyModule(
        __name__,
        globals()["__file__"],
        _import_structure,
        module_spec=__spec__
    )