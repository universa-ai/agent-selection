import sys

if sys.version_info[1] >= 11:
     from typing import Self, override # type: ignore
else:
     from typing_extensions import (
          Self,
          override
     )

from typing import (
    Any,
    List,
    Tuple,
    Dict,
    Type,
    Union,
    Literal,
    Optional,
    Callable,
    ForwardRef,
    TypeVar,
    Mapping,
    Iterator,
    Iterable,
    Annotated,
)

from pydantic import (
     BaseModel,
     TypeAdapter,
     ConfigDict,
     Field,
     create_model,
     field_validator,
     SkipValidation,
     SerializeAsAny,
     ValidationError,
)
from pydantic.fields import FieldInfo
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import PydanticUndefined

# Serialization
SerializedType = Dict[str, Any]
DeserializableType = Union[str, Dict[str, Any]]
