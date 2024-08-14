import os
import inspect
from types import ModuleType
from importlib import import_module

from .utils._types import *


def import_schema(schema_dir: str, schema_name: str) -> ModuleType:
    """
    Import a schema from a given directory.
    """
    _module = import_module("universa")
    for _parent in ["models", *schema_dir.split("/")]:
        _module = getattr(_module, _parent)
    return getattr(_module, schema_name)

class SchemaValidationError(Exception):
    """
    Raised when the schema validation fails.
    """
    __name__ = "SchemaValidationError"  # type: ignore
    __desc__ = "Validation failed.\n{}"

    def __init__(
            self,
            properties: Optional[List[str | int]] = None,
            error_type: Optional[List[str] | str] = None,
            **kwargs
    ) -> None:
        if properties:
            if isinstance(error_type, str):
                error_type = [error_type] * len(properties)
            if error_type:
                self.message = self.__desc__.format(
                    "\n".join([f"- {mp}: {et}" for mp, et in zip(properties, error_type)])
                )
            else:
                self.message = self.__desc__.format(
                    "\n".join([f"- {mp}" for mp in properties])
                )

        super().__init__(self.message, **kwargs)

    @classmethod
    def __name__(cls):
        """
        Return this specific Schema name instead of `ModelMetaclass` for all
        `BaseModel` children.
        """
        return cls.__name__

    @classmethod
    def from_pydantic(cls, e: ValidationError) -> Self:
        """
        Convert a Pydantic validation error to a SchemaValidationError.
        """
        errors = e.errors()
        properties = [error["loc"][0] for error in errors]
        error_type = [f"{error['type']} - {error['msg']}" for error in errors]

        return cls(properties, error_type)


class Schema(BaseModel):
    """
    Simplified pydantic BaseModel schema with custom string representation.
    """
    def __init__(self, *args, **kwargs) -> None:
        """Initialize Schema."""
        try:
            super().__init__(*args, **kwargs)
        except ValidationError as e:
            # Potentially we'll need to handle this differently
            raise SchemaValidationError.from_pydantic(e)
        
    def dict(self) -> Dict[str, Any]:
        """
        Return the schema instance properties as a dictionary.
        """
        return super().model_dump()
    
    @classmethod
    def class_dict(cls) -> Dict[str, Any]:
        """
        Return the schema class properties as a dictionary.
        """
        return cls.model_fields
    
    @classmethod
    def get_schema_dir(cls) -> str:
        """
        Retrieve the name of parent directory of a schema.
        """
        _file = inspect.getfile(cls)
        _parent = os.path.basename(os.path.dirname(_file))
        _file = os.path.basename(_file).split(".")[0]
        return os.path.join(_parent, _file)

    @classmethod
    def validate(
            cls,
            args_to_validate: Dict[str, Any] = {},
            to_dict: bool = False,
            extract_key: Optional[str] = None
    ) -> Union[Self, Dict[str, Any]]:
        """
        Validate given arguments with specified schema.
        """
        # If extracting, raise proper error straight away
        if extract_key and extract_key not in cls.model_fields.keys():
            raise KeyError(f"Key `{extract_key}` not found in schema fields.")

        validated = cls(**args_to_validate)
        
        # Extract key if specified
        if extract_key:
            return validated.dict()[extract_key]
        
        return validated.dict() if to_dict else validated

    @classmethod
    def to_schema(cls) -> JsonSchemaValue:
        """
        Create a JSON Schema for all the parameters of the function.

        Returns:
            Dict[str, Any]: The  schema representation.
        """
        return TypeAdapter(cls).json_schema()

    @classmethod
    def to_str(cls) -> str:
        """
        Return a human-readable representation of the simplified BaseModel schema.

        Args:
            cls: The class representing the schema.

        Returns:
            A string containing the human-readable representation of the schema.
        """
        schema = cls.model_json_schema()
        _str = f"{schema['title']}:"
        for k, v in schema["properties"].items():
            try:
                _str += f"\n- {k}: {v['type']}"
            except KeyError:
                _str += f"\n- {k}: Multiple Types"
            if "default" in v:  # because it can be None
                _str += f" (default: {v['default']})"
        return _str

    @classmethod
    def _get_kwarg_by_order(cls, order: int = 0) -> Any:
        """
        Get the keyword arguments of the schema.
        """
        items = cls.model_fields.items()
        return list(items)[order][0]
    
    @staticmethod
    def create_schema(schema_name: str, **schema_kwargs) -> Type["Schema"]:
        """
        Create a validation schema based on keyword arguments. Used to create schemas
        for input and output of BaseAgent methods. In order to provide a methodology
        to pass generalized inputs between BaseAgents in Nodes, we will use schemas
        as our primary method of validation.

        Args:
            * schema_name (str): Name of the schema
            * schema_kwargs (dict): Keyword arguments for the schema. These should be
            passed as `property_name=property_type` pairs.

        Returns:
            * BaseModel: A pydantic BaseModel class that can be used to validate given arguments.

        Examples:
        1. Creating schema with types only (no default values)

            `create_schema("AgentInput", prompt=str, max_tokens=int)`

        2. Creating schema with optional values (`None` is optional too)

            `create_schema("AgentInput", prompt=str, max_tokens=(int, None))`
        """
        # Prepare kwargs
        for k, v in schema_kwargs.items():
            if isinstance(v, type):
                schema_kwargs[k] = (v, ...)
            elif isinstance(v, tuple):
                schema_kwargs[k] = v

        # Create schema
        return create_model(schema_name, **schema_kwargs, __base__=Schema)