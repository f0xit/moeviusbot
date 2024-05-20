"""This tool contains functions to help loading/saving Python dicts from/to .json-files"""

import datetime as dt
import json
import logging
import os
from typing import Any


class EmptyPathError(IOError):
    pass


def json_ser(obj: object) -> str:
    if isinstance(obj, dt.datetime):
        return obj.isoformat()
    raise TypeError


def load_file(file_path: str, /, encoding: str = "utf-8") -> dict[str, Any] | list[Any]:
    """Opens a JSON-file under the specified path and converts it to a dict.

    Raises EmptyPathError, if the file path is empty.
    Raieses OSError, if reading the file failed.

    Args:
        file_path (str): Path to the given JSON-file, including .json suffix
        encoding (str, optional): Defaults to 'utf-8'.

    Returns:
        dict: The requested JSON-file, parsed as Python dict."""

    if str(file_path) == "":
        raise EmptyPathError("Can't load file, file_path is empty.")

    with open(file_path, "r", encoding=encoding) as file:
        return json.load(file)


def save_file(file_path: str, content: dict, /, indent: int = 4, encoding: str = "utf-8") -> None:
    """Writes the content dict into a JSON-file under the specified path.

    Raises EmptyPathError, if the file path is empty.
    Raieses OSError, if writing the file failed.

    Args:
        file_path (str): Path to the desired JSON-file, including .json suffix
        content (dict): _description_
        indent (int, optional): _description_. Defaults to 4."""

    if str(file_path) == "":
        raise EmptyPathError("Can't save file, file_path is empty.")

    with open(file_path, "w", encoding=encoding) as file:
        json.dump(content, file, indent=indent, default=json_ser)


class DictFile(dict):
    """Extension to the dict type to automatically save the dictionary as a .json-file
    when it is updated. Additionally new dicts can directly by populated with data from
    a file."""

    def __init__(self, name: str, /, suffix: str = ".json", path: str = "json/", load_from_file: bool = True) -> None:
        """Initializes a new dict which is linked to a file.

        By default, it tries to load data from the file when created.
        The usual path for this is ./json/name.json and if the path
        does not exist, the dicts will be created."""

        logging.debug("Initializing DictFile %s ...", name)

        super().__init__()
        self.file_name = path + name + suffix

        if not os.path.exists(path):
            os.makedirs(path)
            logging.debug("Created dirs for path %s", path)

        if not load_from_file:
            return

        value = load_file(self.file_name)

        if not isinstance(value, dict):
            return

        self.update(json_file)

        logging.debug("Loaded data from file %s. %s keys.", self.file_name, len(value.keys()))

        logging.info("DictFile %s initialized succesfully.", self.file_name)

    def __setitem__(self, __key: str, __value: Any) -> None:
        super().__setitem__(__key, __value)

        logging.debug("DictFile %s item set. %s: %s", self.file_name, __key, __value)

        save_file(self.file_name, self)

    def update(self, __m) -> None:
        super().update(__m)

        logging.debug("DictFile %s updated", self.file_name)

        save_file(self.file_name, self)

    def pop(self, key):
        item = super().pop(key)

        logging.debug("DictFile %s popped.", self.file_name)

        save_file(self.file_name, self)

        return item

    def save(self):
        save_file(self.file_name, self)
