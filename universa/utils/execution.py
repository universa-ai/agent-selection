import re
import functools
from typing import Any, Callable, Union, Tuple

from .logs import general_logger


def retry(num_retries: int = 2):
    """
    Simple retrying decorator. Will raise an error only if all attempts fail.

    Args:
        num_retries (int): Number of retries.

    Returns:
        Any: Any return value of the decorated function.

    Raises:
        Exception: Any exception raised by the decorated function.
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            _exc = None
            for i in range(num_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if isinstance(e, TypeError):  # we handle this in keyword_fallback
                        raise e
                    _exc = e
                    general_logger.warning(
                        f"Error in {func.__name__} at {i+1} attempt: {e}"
                    )
                    pass
            if isinstance(_exc, Exception):
                raise _exc
            else:
                raise Exception(f"Function {func.__name__} failed {num_retries} times")
        return wrapper
    return decorator

def keyword_fallback(func: Callable):
    """
    Decorator to provide fallback for missing keyword arguments.

    Args:
        func (Callable): Function to decorate.

    Returns:
        Any: Any return value of the decorated function.
    """
    def wrapper(*args, **kwargs) -> Any:
        try:
            return func(*args, **kwargs)
        except TypeError as e:
            msg = e.args[0]
            if 'keyword argument' in msg:
                arg = msg.split('keyword argument ')[1].split(' ')[0]
                arg = re.sub(r"'([^']*)'", r"\1", arg)
                general_logger.warning(
                    f"Invalid keyword argument: {arg} - retrying without it."
                )
                kwargs.pop(arg)
                return keyword_fallback(func)(*args, **kwargs)
            raise
    return wrapper

def request_user_input(
        message: str,
        response_type: type,
        ranges: Tuple[int, int] = None
) -> Union[str, int]:
    """
    Request user input.

    Returns:
        str: User input.
    """
    if not message.strip().endswith(':'):
        message += ':'
    if not message.endswith('\n'):
        message += '\n'

    result = input(message)

    if response_type is int:
        while not result.isdigit():
            print('Invalid input. Please enter a number.')
            result = input(message)
        if ranges:
            result = int(result)
            while not ranges[0] <= result <= ranges[1]:
                print(f'Invalid input. Please enter a number between {ranges[0]} and {ranges[1]}.')
                result = input(message)
        return int(result)
    
    return result
