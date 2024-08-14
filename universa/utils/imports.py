import os
import sys
import pkgutil
import importlib
from types import ModuleType
from typing import Any, Iterable, List, Optional

import importlib
import importlib.metadata as importlib_metadata

from .logs import get_logger


import_logger = get_logger("Import Utility")


def get_parent_path(path: str, levels: int = 1) -> str:
    """
    Get parent path of a given path.

    Args:
        * path (str): Path to get parent of.
        * levels (int): How many levels to go up.

    Returns:
        str: Parent path of the given path.
    """
    for _ in range(levels):
        path = os.path.dirname(path)
    return os.path.abspath(path)

def import_class(class_name: str) -> Any:
    """
    Import a class by name in the wild. This is possible
    thanks to LazyModule used for lazily importing all the modules.
    """
    return getattr(importlib.import_module("universa"), class_name)

def check_import(package: str) -> bool:
    """
    Check if a package is available.
    """
    try:
        importlib_metadata.version(package)
        return True
    except importlib_metadata.PackageNotFoundError:
        import_logger.error(f"Package {package} not found.")
        return False

def build_all_paths(structure, current_path: Optional[list] = None, result: Optional[dict] = None):
    """
    Recursively build a dictionary of all paths from a nested dictionary.
    """
    if result is None:
        result = {}
    if current_path is None:
        current_path = []

    for key, value in structure.items():
        if isinstance(value, dict):
            build_all_paths(value, current_path + [key], result)
        else:
            result[key] = current_path
            for item in value:
                result[item] = current_path + [key]
    return result

def build_top_paths(structure: dict, current_path: Optional[str] = None):
    """
    Recursively build a dictionary of all possible paths for given nested dictionary.
    """
    paths = []
    for key, value in structure.items():
        if isinstance(value, dict):
            for sub_path in build_top_paths(value, key):
                paths.append(f"{sub_path}")
        else:
            for item in value:
                paths.append(
                    f"{key}.{item}"
                    if current_path is None
                    else f"{current_path}.{key}.{item}"
                )

    return paths

def get_all_attributes(structure, attrs=None):
    """
    Recursively retrieve all names that exist in the nested dictionary.
    """
    if attrs is None:
        attrs = []

    for key, value in structure.items():
        attrs.append(key)
        if isinstance(value, dict):
            get_all_attributes(value, attrs)
        else:
            for item in value:
                attrs.append(item)

    return list(set(attrs))

def import_specific_modules(module_addresses: List[str]) -> None:
    """
    Dynamically imports a list of modules from the list of modules addresses.
    If a module is already imported, it is skipped.

    Args:
        module_addresses (List[str]): A list of address of modules to be imported.

    Returns:
        None
    """
    for address in module_addresses:
        if address in sys.modules:
            continue
        importlib.import_module(address)

def import_modules_from_directory(directory: str) -> List[str]:
    """
    Import all modules from a certain directory.

    Args:
        directory (str): The directory path from which to import the modules.

    Returns:
        List[str]: A list of module addresses that were imported.
    """
    module_addresses = []
    for module_info in pkgutil.iter_modules([directory]):
        module_address = directory.replace("/", ".") + "." + module_info.name
        module_addresses.append(module_address)

    if len(module_addresses) == 0:
        raise ModuleNotFoundError(
            f"Invalid directory address. Please make sure that the directory address is correct. Address: {directory}"
        )
    import_specific_modules(module_addresses)
    return module_addresses

class LazyModule(ModuleType):
    """
    Module class that surfaces all objects but only performs associated imports when the objects are requested.

    Modified from:
    https://github.com/huggingface/diffusers/blob/main/src/diffusers/utils/import_utils.py

    Changes are pointed with a comment.
    """

    def __init__(
        self, name, module_file, import_structure, module_spec=None, extra_objects=None
    ):
        super().__init__(name)

        # Create all possible imports
        self._class_to_module = build_all_paths(import_structure)

        # Create all top level modules
        self._modules = set(import_structure.keys())

        # Needed for autocompletion in an IDE
        self.__all__ = get_all_attributes(
            import_structure
        )  # create all attributes of given imports
        self.__file__ = module_file
        self.__spec__ = module_spec
        self.__path__ = [os.path.dirname(module_file)]
        self._objects = {} if extra_objects is None else extra_objects
        self._name = name
        self._import_structure = import_structure

    def __dir__(self):
        """
        The elements of self.__all__ that are submodules may or may not be in the dir already, depending on whether
        they have been accessed or not. So we only add the elements of self.__all__ that are not already in the dir.

        Needed for autocompletion in an IDE.
        """
        result: List[str] = list(super().__dir__())

        for attr in self.__all__:
            if attr not in result:
                result.append(attr)
        return result

    def __getattr__(self, name: str) -> Any:
        """
        Method used when import from.
        """
        if name in self._objects:
            return self._objects[name]

        if name in self._modules:
            value = self._get_module(name)

        elif name in self._class_to_module.keys():
            # Get the module and then create the whole import path
            _modules = self._class_to_module[name]
            module = self._get_module(".".join(_modules))
            value = getattr(module, name)

        else:
            raise AttributeError(f"module {self.__name__} has no attribute {name}")

        setattr(self, name, value)

        return value

    def _get_module(self, module_name: str):
        """
        Import given module.
        """
        try:
            return importlib.import_module("." + module_name, self.__name__)
        except Exception as e:
            raise RuntimeError(
                f"Failed to import {self.__name__}.{module_name} because of the following error (look up to see its"
                f" traceback):\n{e}"
            ) from e

    def __reduce__(self):
        """
        This method is used to ensure that the LazyModule object can be pickled and unpickled correctly.
        """
        return (self.__class__, (self._name, self.__file__, self._import_structure))
