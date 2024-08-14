# Tools

Tools are pre-defined Python functions that an agent can utilize. They give Agents access to various powerful capabilities such as performing complex mathematical calculations, browsing the internet, manipulating files, executing shell commands, etc. Providing tools can not only increase the AI Agents capabilities, it can also increase the accuracy of an Agent's responses.

## JSON Schema of a Tool

In order for an Agent to use a tool, we cannot simply tell the Agent which functions it can make use of. Instead we have to create JSON schemas for each tools

The `BaseTool` represents a tool/method for an Agent to execute python functions. An instance of it will contain the Pydantic Schemas for the parameters and the return type of the tool. These Schemas are the key to generate the JSON formatted schema that can be passed to OpenAI models and its variants for tool calling.

To create a JSON schema for a tool, we first have to write a method that has:

- Proper annotations for all the parameters, and return value.
- A Google Style docstring (See more examples of Google Style docstring from [here](https://gist.github.com/redlotus/3bc387c2591e3e908c9b63b97b11d24e)). Although this is optional, providing it is highly recommended as it will provide proper descriptions not only for the method itself but also for all the parameters of the method.

The following example shows a method with proper annotations and docstring:

```python
from typing import List, Optional

def function_with_proper_docstring(param1: List[str], param2: Optional[int] = None) -> bool:
    """
    Example function with types documented in the docstring.
    Please note that the parameter type in the docstring is optional.
    So parameters can also be written like this: 'param1: The description of param1'

    Args:
        param1 (List[str]): The description of the first parameter.
        param2 (Optional[str]): The description of the second parameter.

    Returns:
        bool: The description of the return value. True for success, False otherwise.
    """

    # Your code
    ...
```
Once the method is written with proper annotations and docstring, all we have to do is simply create a `BaseTool` instance by passing the method and then invoke `get_function_schema()` of the respective model class.

Following is an example for creating JSON schemas to use with OpenAI models.  
```python
from universa.tools.tool import BaseTool
from universa.models.openai import OpenAI

a_tool = BaseTool.from_function(google_search)
json_schema = OpenAI.get_function_schema()
```

The result will be the JSON schema of the function as required by OpenAI and its variant models

```python
{
    "type": "function",
    "function": {
        "description": "Example function with types documented in the docstring. Please note that the parameter type in the docstring is optional. So in the Arg section we can also write 'param1: The description of param1'",
        "name": "function_with_proper_docstring",
        "parameters": {
            "properties": {
                "param1": {
                    "description": "The description of the first parameter.",
                    "items": {"type": "string"},
                    "title": "Param1",
                    "type": "array",
                },
                "param2": {
                    "anyOf": [{"type": "integer"}, {"type": "null"}],
                    "default": None,
                    "description": "The description of the second parameter.",
                    "title": "Param2",
                },
            },
            "required": ["param1"],
            "title": "function_with_proper_docstring_input_schema",
            "type": "object",
        },
    },
}
```

## Registering a Tool

Most of the time, we don't need to manually create a JSON schema of a method as shown above and then pass it to an agent. If we want our Agents to use a tool, we can follow these simple instructions:

- Create a python module, `some_tool.py`, then store it inside the `universa/tools/extensions` directory.
- Inside the script, write the function giving the proper annotations and a docstring as mentioned earlier.
- Import `ToolRegistry` class and add `@ToolRegistry.register_tool` decorator to your function.

To register the `function_with_proper_docstring()` function mentioned above, we have to do the following:

```python
from ..tool import ToolRegistry
from typing import List, Optional


@ToolRegistry.register_tool
def function_with_proper_docstring(param1: List[str], param2: Optional[int] = None) -> bool:
    """
    Example function with types documented in the docstring.
    Please note that the parameter type in the docstring is optional.
    So parameters can also be written like this: 'param1: The description of param1'

    Args:
        param1 (List[str]): The description of the first parameter.
        param2 (Optional[str]): The description of the second parameter.

    Returns:
        bool: The description of the return value. True for success, False otherwise.
    """

    # Your code
    ...
```

And that's it. In this way, we can give out Agents as many tools as we want. **_IMPORTANT NOTE: a module must NOT contain more than one function. Hence, all functions has to be stored in separate modules._**

## Creating Agents with tools

We can create Agents who can use any of the registered tools. We can give the Agent either all tools or some tools to utilize. To create an Agent who has access to all the registered tools, we simply have to pass the optional `available_tools` attribute by setting it `"all"` when creating a `BaseAgent` class instance.

```python
agent = BaseAgent(
    available_tools="all",
    ...
    # other configs
)
```

Sometimes it's not the best idea to give an Agent all of the tools to use because in that way, there is no option for creating specialized Agents. Therefore, if we want to create an Agent who has access to only specific tools, we can pass in the list of module names that contain those tools.

```python
agent = BaseAgent(
    available_tools=["web_scraper"],
    ...
    # other configs
)
```

**_REMEMBER: The list must contain the names of the modules without the extension `.py`. Do NOT provide the list of function names._**
