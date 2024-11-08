import os
import json
import inspect
from abc import ABC

from .schema import Schema, import_schema

from .utils._types import *
from .utils.logs import get_logger
from .utils.imports import import_class
from .utils.registry import generate_id


class Executable(ABC):
    """
    Interface for executable objects such as Agents, Generative Models, Tools, etc.

    For the purpose of serialization this class also provides two core methods:
    * `to_json` - creates a JSON compatible serialzied structure of a model instance
    * `from_json` - loads a model instance from previously serialized structure or JSON file
    """

    input_schema: Type[Schema]
    output_schema: Type[Schema]
    message_schema: Type[Schema]

    def register(self, object_id: Optional[str] = None) -> None:
        """
        Register the model in the registry.
        """
        self.object_id = object_id or generate_id()
        self.logger = get_logger(self.__class__.__name__)

    def get_id(self) -> str:
        """
        Return the ID of the executable.
        """
        return self.object_id
    
    def _get_model_dir(self) -> Optional[str]:
        """
        Retrieve the name of parent directory of a model.
        """
        schema: Any = getattr(self, "input_schema", None)
        if schema is None:
            schema: Any = getattr(self, "output_schema", None)

        if issubclass(type(schema), Schema):
            return schema.get_schema_dir()
    
        return None
    
    def to_json(
            self,
            save_path: Optional[str] = None,
            exist_ok: bool = False
    ) -> SerializedType:
        """
        Serialize the model instance. It aims to provide a method for creating
        JSON compatible formats from created instances of models.

        Each base class that inherits from AbstractModel should implement this method,
        as there are specific differences between them.

        Args:
            save_path (str): Path to save the serialized model instance.
            exist_ok (bool): If True, it will overwrite the file if it exists.

        Returns:
            SerializedType: Serialized model instance.
        """
        # Prepare the schema
        _serialized = {
            "object_id": self.object_id,
            "base_class": self.__class__.__name__,
            "model_dir": self._get_model_dir(),
            "schemas": {}
        }

        # Get the attributes of the constructor
        _vars = vars(self)
        init_keys = inspect.signature(self.__init__).parameters.keys()
        constructor_args = {item: _vars.get(item, None) for item in init_keys}

        # Gather & divide attributes
        for attr, val in constructor_args.items():
            if inspect.isclass(val) and issubclass(val, Schema):
                _serialized["schemas"][attr] = val.__name__
            else:
                try:
                    json.dumps(val)
                except TypeError:
                    self.logger.warning(f"Attribute `{attr}` is not JSON serializable - skipping.")
                    val = None
                _serialized[attr] = val

        # Save if path is provided
        if save_path:
            self.save_json(
                path=save_path,
                data=_serialized,
                exist_ok=exist_ok
            )
        
        return _serialized

    @classmethod
    def from_json(cls, serialized: DeserializableType, only_args: bool = False) -> Union[Self, Dict[str, Any]]:
        """
        Deserialize the model instance.

        Args:
            serialized (DeserializableType): Serialized CoreModel instance, either
            a dictionary, a path to a JSON file, or a default name (see `schemas/examples/__init__.py`).
            only_args (bool): If True, it will return only the constructor arguments.

        Returns:
            Deserialized model instance of a specific type or consturctor arguments.
        """
        if isinstance(serialized, str):
            serialized = cls.load_json(serialized)

        # Check if the class it's called from is correct
        base_cls = serialized.get("base_class", cls.__name__)
        base_cls = import_class(base_cls)

        if not issubclass(base_cls, cls):
            raise ValueError(
                f"Deserialized class `{base_cls}` is not a subclass of `{cls}`."
            )
        
        constructor_args = {}

        # Build constructor arguments
        schema_dir = serialized.get("model_dir", None)
        for _attr, _vals in serialized.items():
            if _attr == "schemas":
                # Import all the schemas
                for schema_k, schema_v in serialized.get("schemas", {}).items():
                    _schema = import_schema(
                        schema_dir=schema_dir,
                        schema_name=schema_v
                    )
                    constructor_args[schema_k] = _schema
                    
            elif _attr != "base_class" and _attr != "model_dir":
                constructor_args[_attr] = _vals

        return base_cls(**constructor_args) if not only_args else constructor_args

    @staticmethod
    def save_json(
        data: SerializedType,
        path: str,
        exist_ok: bool = False
    ) -> None:
        """
        Save the serialized data to a file.
        """
        if os.path.exists(path) and not exist_ok:
            raise FileExistsError(f"File already exists at {path}.")
        with open(path, "w") as f:
            json.dump(data, f, indent=4)

    @staticmethod
    def load_json(path: str) -> SerializedType:
        """
        Load the serialized data from a file.
        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"File not found at {path}.")
        with open(path, "r") as f:
            return json.load(f)
        
    @staticmethod
    def retrieve_env_key(env_name: Union[str, List[str]]) -> str:
        """
        Retrieve a key from the environment.
        """
        if isinstance(env_name, str):
            env_name = [env_name]
        
        # Check if given key is in the environment
        for env_name in env_name:
            retrieved_key = os.environ.get(env_name, None)
            if retrieved_key: break
        if not retrieved_key:
            raise ValueError(f"No keys under name(s) `{env_name}` found.")
        
        return retrieved_key
