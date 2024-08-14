import inspect

from docstring_parser import parse, compose, common
from docstring_parser.common import DocstringStyle

from ..core import Executable

from ..schema import Schema
from .tool_schema import ToolCall, ToolCallResult

from ..utils.registry import Registry
from ..utils.logs import get_logger
from ..utils._types import *


logger = get_logger(__name__)


class MissingAnnotationError(Exception):
    """
    Raised when the function is missing annotations for required parameters.
    """
    __name__ = "MissingAnnotationError"
    __desc__ = "The parameters `{}` is missing annotations. "

    def __init__(self, missing: List[str], **kwargs) -> None:
        self.message = self.__desc__.format(missing)
        super().__init__(self.message, **kwargs)


class DocstringParseError(Exception):
    """
    Raised when the docstring is not in the correct format.
    """
    __name__ = "DocstringParseError"
    __desc__ = "Incorrect docstring format. Please follow the Google Style docstring format. Following errors occurred during parsing: \n{}"

    def __init__(self, issues: Iterable[str], **kwargs) -> None:
        self.message = self.__desc__.format("\n".join(issues))
        super().__init__(self.message, **kwargs)


class ToolRegistrationError(Exception):
    """
    Exception raised when an error occurs while registering a tool.
    """
    __name__ = "ToolRegistrationError"
    __desc__ = "Error occurred while registering the tool. {}"

    def __init__(self, message: str, **kwargs) -> None:
        self.message = self.__desc__.format(message)
        super().__init__(self.message, **kwargs)


class Docstring:
    """
    A class to represent the docstring of a function.
    This class stores several information from the Google Style docstring of a function.
    """
    def __init__(
        self,
        func: Callable[..., Any],
        description: str,  # description of the function
        args: Optional[Dict[str, str]] = None,  # key: arg name, value: arg description
        returns_desc: Optional[str] = None,  # description of the return value
        from_docstring_parser: Optional[common.Docstring] = None,
    ) -> None:
        self.func = func
        self.description = description
        self.args = args
        self.returns_desc = returns_desc
        self.from_docstring_parser = from_docstring_parser

    @staticmethod
    def remove_new_lines(text: str) -> str:
        """
        Remove new lines from the description.
        """
        return text.replace("\n", " ").strip()

    @classmethod
    def extract_description(
        cls,
        parsed_docstring: common.Docstring,
        func: Callable[..., Any],
    ):
        """
        Extract the description from the parsed docstring.
        """
        description = parsed_docstring.description
        if description is None or len(description) == 0:
            logger.warning(
                f"Incorrect docstring format. Function '{func.__name__}' is missing return value description."
            )
            description = func.__name__.replace("_", " ")
        else:
            _desc = parsed_docstring.description
            if _desc is not None:
                description = cls.remove_new_lines(_desc)
        return description

    @classmethod
    def extract_params(
        cls,
        parsed_docstring: common.Docstring,
        func: Callable[..., Any],
    ) -> Dict[str, Any]:
        """
        Extract the parameters from the parsed docstring.
        """
        if len(parsed_docstring.params) == 0:
            logger.warning(
                f"Incorrect docstring format. Function '{func.__name__}' is missing parameter descriptions. Each parameter descriptions will be in Parameter '<param_name>' format."
            )

        args = {
            param.arg_name: cls.remove_new_lines(param.description) 
            if param.description else f"Parameter '{param.arg_name}'"
            for param in parsed_docstring.params
        }

        return args

    @classmethod
    def extract_returns(
        cls,
        parsed_docstring: common.Docstring,
        func: Callable[..., Any],
    ):
        """
        Extract the return value from the parsed docstring.
        """
        returns = parsed_docstring.returns
        if returns is None or returns.description is None or returns.description == "":
            logger.warning(
                f"Incorrect docstring format. Function '{func.__name__}' is missing return value description."
            )
            returns_desc = "The return value."
        else:
            returns_desc = cls.remove_new_lines(returns.description)
        return returns_desc

    @classmethod
    def from_function(cls, func: Callable[..., Any]) -> Self:
        """
        Create a Docstring object from a function.

        Args:
            func (Callable[..., Any]): The function for which the docstring is to be created.

        Returns:
            Docstring: A Docstring object created from the docstring.

        Raises:
            None

        Examples:
            >>> def my_function(param1, param2):
            ...     '''
            ...     This is a sample function.
            ...
            ...     Args:
            ...         param1: The first parameter.
            ...         param2: The second parameter.
            ...
            ...     Returns:
            ...         The result of the function.
            ...     '''
            ...     return param1 + param2
            ...
            >>> docstring = Docstring.from_function(my_function)
            >>> print(docstring.description)
            This is a sample function.
            >>> print(docstring.args)
            {'param1': 'The first parameter.', 'param2': 'The second parameter.'}
            >>> print(docstring.returns)
            The result of the function.
        """
        try:
            _doc = func.__doc__
            if _doc is not None:
                parsed_docstring = parse(_doc, style=DocstringStyle.GOOGLE)
        except Exception as e:
            raise DocstringParseError(issues=e.args)

        description = cls.extract_description(parsed_docstring, func)
        args = cls.extract_params(parsed_docstring, func)
        returns_desc = cls.extract_returns(parsed_docstring, func)

        return cls(func, description, args, returns_desc, parsed_docstring)

    def get_function_description(self) -> str:
        """
        Get the description of the function.

        Returns:
            str: The description of the function.
        """
        return self.description

    def get_param_description(self, param_name: str) -> str:
        """
        Get the description of a parameter.

        Args:
            param_name (str): The name of the parameter.

        Returns:
            str: The description of the parameter.
        """

        if self.args is None:
            logger.warning(
                f"Incorrect docstring format. Function '{self.func.__name__}' is missing parameter description for '{param_name}'."
            )
            return f"Parameter '{param_name}'"
        
        param_desc = self.args.get(param_name, None)
        if param_desc is None or len(param_desc) == 0:
            logger.warning(
                f"Incorrect docstring format. Function '{self.func.__name__}' is missing parameter description for '{param_name}'."
            )
            return f"Parameter '{param_name}'"

        return param_desc

    def get_return_description(self) -> Optional[str]:
        """
        Get the description of the return value.

        Returns:
            str: The description of the return value.
        """
        return self.returns_desc

    def __str__(self):
        if self.from_docstring_parser is not None:
            return compose(
                docstring=self.from_docstring_parser,
                style=DocstringStyle.GOOGLE,
            )
        else:
            return ""

class BaseTool(Executable):
    """
    Base class for methods and functions.
    """
    def __init__(
        self,
        name: str,
        description: str,
        docstring: Docstring,
        func: Callable[..., Any],
        input_schema: Type[Schema],
        output_schema: Type[Schema],
    ) -> None:
        """
        Initialize function.
        """
        self.name = name
        self.description = description
        self.docstring = docstring
        self.func = func
        self.input_schema = input_schema
        self.output_schema = output_schema

    @staticmethod
    def get_verified_annotation(annotation: Any) -> Any:
        """Handle the forward references of a parameter and avoid taking Callable types.

        Args:
            annotation (Any): The annotation of the parameter.

        Returns:
            Any: The type annotation of the parameter.
        """
        if isinstance(annotation, str):
            return ForwardRef(annotation)
        if annotation.__name__ == "Callable":
            raise ValueError(
                "Callable type annotations are not supported. Please use a more specific type."
            )
        else:
            return annotation

    @staticmethod
    def get_param_info(
        param: inspect.Parameter,
        docstring: Docstring,
    ) -> Tuple[Any, FieldInfo]:
        
        # Get the verified annotation. Checks for Callable type and Forward References
        param_annotation = BaseTool.get_verified_annotation(param.annotation)
        default = (
            PydanticUndefined
            if param.default is inspect.Parameter.empty
            else param.default
        )

        # Get the description of the parameter
        if hasattr(param_annotation, "__metadata__"):
            if not isinstance(param_annotation.__metadata__[0], str):
                raise ValueError(
                    f"Description of parameter:'{param.name}' must be a string."
                )
            description = param_annotation.__metadata__[0]
        else:
            # If the description is not provided in the annotation, extract it from the docstring
            description = docstring.get_param_description(param.name)
        return param_annotation, FieldInfo(default=default, description=description)

    @classmethod
    def from_function(cls, func: Callable) -> Self:
        """
        This method creates a BaseTool object with Pydantic model of input, output schemas.
        The instance of this BaseTool class is later used to create the JSON representation of
        the containing function in the format required by OpenAI, and its variants, from the input schema.

        Args:
            func (Callable): The Python method to wrap.

        Returns:
            BaseTool: An instance of the BaseTool class.

        Raises:
            ValueError: If the input is not a callable.
            MissingAnnotationError: If a parameter is missing annotations.
        """
        assert isinstance(func, Callable), "Input must be a callable."

        docstring = Docstring.from_function(func)
        func_args = {}
        func_spec = inspect.signature(func)
        for _, v in func_spec.parameters.items():
            # Throw an error if the parameter is missing annotations
            if v.annotation is inspect.Parameter.empty:
                raise MissingAnnotationError([v.name])

            annotation, field_info = BaseTool.get_param_info(v, docstring)
            func_args[v.name] = (annotation, field_info)

        input_schema = Schema.create_schema(
            func.__name__ + "_input_schema", **func_args
        )

        return_type = func_spec.return_annotation
        if return_type is inspect.Signature.empty or return_type is None:
            logger.warning(
                f"Function {func.__name__} is missing a proper return type annotation."
                " Although it is not required, it is recommended to add an appropriate one."
            )
            return_type = Any

        output_schema = Schema.create_schema(
            func.__name__ + "_output_schema", output=(return_type, ...)
        )

        return cls(
            name=func.__name__,
            description=docstring.get_function_description(),
            docstring=docstring,
            func=func,
            input_schema=input_schema,
            output_schema=output_schema,
        )

    @staticmethod
    def execute_tool(
        tool_call_infos: List[ToolCall],
        tool_registry: "ToolRegistry",
    ) -> Dict[str, ToolCallResult]:
        """
        Executes the function with the given arguments and keyword arguments.
        Input type has to satisfy the input_schema and the return type is output_schema.
        """
        results: Dict[str, ToolCallResult] = {}

        for tool_call_info in tool_call_infos:

            # prepare function data from tool call
            function_name = tool_call_info.function_name
            function_args = tool_call_info.function_params

            # Get the function from the tool registry
            function = tool_registry.get_tool(function_name)

            if not isinstance(function, BaseTool):
                raise ValueError(
                    f"Function: {function_name} is not available in the tool registry."
                )

            # Create input schema to validate whether input format is correct
            input = function.input_schema.validate(function_args, to_dict=True)

            # Execute the function
            logger.info(f"Executing function: {function_name} with input: {input}")
            if isinstance(input, dict):
                execution_result = function.func(**input)

            # Store the result
            id = tool_call_info.get_tool_call_id()
            results[id] = ToolCallResult(
                function_name=function_name,
                result=execution_result,
            )

        return results

    def __str__(self) -> str:
        """
        Return a string representation of the object.

        This method returns a string that represents the object. It includes the name of the function,
        its description, and arguments.

        Returns:
            str: A string representation of the object.
        """
        _doc = getattr(self, "_doc", self.__doc__)
        _name = getattr(self, "_name", self.__class__.__name__)
        _json_schema = getattr(self, "input_schema", None)
        _str = f"{_name}"
        if _doc:
            _str += f"\n\t{_doc.strip()}"
        if _json_schema:
            _str += f"\n{_json_schema.to_str()}"  # requires schema to by of type Schema, not BaseModel

        return _str

class ToolRegistry(Registry):
    """
    Registry for tools. It allows for storing import paths to methods and their names & descriptions,
    so that we could simply choose the methods from here.
    """
    # Contains all the tools/methods by key value pair where the key is the name of the module where it is stored.
    registered_tools: Dict[str, BaseTool] = {}

    T = TypeVar("T")

    def __init__(
        self,
        available_tools: Optional[Dict[str, BaseTool]] = None,
    ) -> None:
        self.available_tools = available_tools if available_tools else {}

    @classmethod
    def register_tool(cls, func: Callable[..., T]) -> Callable[..., T]:
        """
        Registers a tool function in the tool registry - to be used as a decorator.
        The keys in the registry are the module addresses where the tool functions are stored.
        And the values are the BaseTool instances of the tool functions.

        Args:
            func: The tool function to be registered.

        Returns:
            The registered tool function.
        """
        if func.__module__ in cls.registered_tools:
            raise ToolRegistrationError(
                f"Module: '{func.__module__}' for the tool: '{func.__name__}' already exists. Use a different name for the module. "
            )

        func_obj = BaseTool.from_function(func)
        cls.registered_tools[func.__module__] = func_obj

        return func

    def add_tool(self, func: Callable[..., Any]) -> None:
        """
        Method for adding tool instead of the register_tool decorator.

        Parameters:
        - func: The function to be added as a tool.
        - description: Optional description for the tool.

        Returns:
        None
        """
        func_obj = BaseTool.from_function(func)
        self.registry["tools"][func_obj.name] = func_obj

    def get_tool(self, tool_name) -> Optional[BaseTool]:
        """
        Retrieve a tool from the registry. It returns the BaseTool instance of the tool.

        Args:
            tool_name (str): The name of the tool to retrieve.

        Returns:
            BaseTool: The BaseTool instance from the registry.
        """
        return self.available_tools.get(tool_name, None)

    def get_tools_as_schema(
            self, 
            func: Callable[[BaseTool], JsonSchemaValue]
    ) -> List[JsonSchemaValue]:
        """
        Fetch all available tools in the registry as JSON schema.

        Returns:
            A list of JsonSchemaValue objects representing the available tools in the registry.
        """
        return [func(tool) for tool in self.available_tools.values()]

    def remove_tool(self, tool_name) -> JsonSchemaValue:
        """
        Remove a tool from the registry.

        Args:
            tool_name (str): The name of the tool to be removed.

        Returns:
            JsonSchemaValue: The removed tool.
        """
        return self.registry.pop(tool_name)

    @classmethod
    def from_tool_names(cls, tool_names: List[str]) -> Self:
        """
        Create a new instance of ToolRegistry with only the specified tool names.

        Args:
            tool_names (Optional[List[str]]): A list of tool names to include in the new ToolRegistry instance.

        Returns:
            ToolRegistry: A new instance of ToolRegistry containing only the specified tools.
        """
        filtered_tools: Dict[str, BaseTool] = {}

        for tool_name in tool_names:
            if tool_name in cls.registered_tools:
                tool = cls.registered_tools[tool_name]
                if tool.name in filtered_tools:
                    raise ToolRegistrationError(
                        f"Tool with the name: '{tool.name}' already exists in the registry."
                        " Use a different name for the tool."
                    )
                filtered_tools[tool.name] = tool
            else:
                logger.warning(
                    f"WARNING: Tool: {tool_name} is not available in the registry."
                )

        return cls(available_tools=filtered_tools)

    @classmethod
    def list_registered_tools(cls) -> Dict[str, BaseTool]:
        """
        List all available methods in the registry

        Returns:
            A list of BaseTool objects representing the available tools in the registry.
        """

        return cls.registered_tools
    