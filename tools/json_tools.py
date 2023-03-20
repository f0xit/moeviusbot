'''This tool contains functions to help loading/saving Python dicts from/to .json-files'''

import json
import logging
import os
from typing import Any

from result import Err, Ok, Result


def load_file(
    file_path: str,
    /,
    encoding: str = 'utf-8'
) -> Result[dict, str]:
    """Opens the file under the specified path and converts it to a dict.
    If the file could not be found or the file path is empty, the function returns None.

    Args:
        file_path (str): _description_
        encoding (str, optional): _description_. Defaults to 'utf-8'.

    Returns:
        dict | None: _description_"""

    if str(file_path) == '':
        return Err('Can\'t save file, file_path is empty.')

    try:
        with open(file_path, 'r', encoding=encoding) as file:
            return Ok(json.load(file))
    except OSError as err_msg:
        return Err(f'Could not read file {file_path}! Exception: {err_msg}')


def save_file(
    file_path: str,
    content: dict,
    /,
    indent: int = 4,
    encoding: str = 'utf-8'
) -> Result[str, str]:
    """Writes the content dict into a file under the specified path.

    If the file could not be found or the file path is empty, the function returns False,
    otherwise it returns True.

    Args:
        file_path (str): _description_
        content (dict): _description_
        indent (int, optional): _description_. Defaults to 4.

    Returns:
        bool: _description_
    """

    if str(file_path) == '':
        return Err('Can\'t save file, file_path is empty.')

    try:
        with open(file_path, 'w', encoding=encoding) as file:
            json.dump(content, file, indent=indent)
            return Ok(f'File {file_path} saved succesfully.')
    except OSError as err_msg:
        return Err(f'Could not read file {file_path}! Exception: {err_msg}')


class DictFile(dict):
    '''Extension to the dict type to automatically save the dictionary as a .json-file
    when it is updated. Additionally new dicts can directly by populated with data from
    a file.'''

    def __init__(
        self,
        name: str,
        /,
        suffix: str = '.json',
        path: str = 'json/',
        load_from_file: bool = True
    ) -> None:
        '''Initializes a new dict which is linked to a file.

        By default, it tries to load data from the file when created.
        The usual path for this is ./json/name.json and if the path
        does not exist, the dicts will be created.'''

        logging.debug(
            'Initializing DictFile %s ...', name
        )

        super().__init__()
        self.file_name = path + name + suffix

        if not os.path.exists(path):
            os.makedirs(path)
            logging.debug(
                'Created dirs for path %s', path
            )

        if load_from_file:
            match load_file(self.file_name):
                case Ok(value):
                    self.update(value)

                    logging.debug(
                        'Loaded data from file %s. %s keys.',
                        self.file_name, len(value.keys())
                    )

                case Err(err_msg):
                    logging.error(err_msg)
                    return

        logging.info(
            'DictFile %s initialized succesfully.', self.file_name
        )

    def __setitem__(self, __key: str, __value: Any) -> None:
        super().__setitem__(__key, __value)

        logging.debug(
            'DictFile %s item set. %s: %s',
            self.file_name, __key, __value
        )

        save_file(self.file_name, self)

    def update(self, __m) -> None:
        super().update(__m)

        logging.debug('DictFile %s updated', self.file_name)

        save_file(self.file_name, self)

    def pop(self, key):
        item = super().pop(key)

        logging.debug('DictFile %s popped.', self.file_name)

        save_file(self.file_name, self)

        return item
