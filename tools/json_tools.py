'''This tool contains functions to help loading/saving Python dicts from/to .json-files'''

import json
import logging
import os
from typing import Any


def load_file(file_path: str, /, encoding: str = 'utf-8') -> dict | None:
    """Opens the file under the specified path and converts it to a dict.
    If the file could not be found or the file path is empty, the function returns None.

    Args:
        file_path (str): _description_
        encoding (str, optional): _description_. Defaults to 'utf-8'.

    Returns:
        dict | None: _description_
    """

    if str(file_path) == '':
        logging.warning('Can\'t save file, file_path is empty.')
        return None

    try:
        with open(file_path, 'r', encoding=encoding) as file:
            logging.debug('File %s opened succesfully.', file_path)
            return json.load(file)
    except OSError as err_msg:
        logging.error(
            'Could not read file %s! Exception: %s', file_path, err_msg
        )
        return None


def save_file(file_path: str, content: dict, /, indent: int = 4, encoding: str = 'utf-8') -> bool:
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
        logging.warning('Can\'t save file, file_path is empty.')
        return False

    try:
        with open(file_path, 'w', encoding=encoding) as file:
            json.dump(content, file, indent=indent)
            logging.debug('File %s saved succesfully.', file_path)
            return True
    except OSError as err_msg:
        logging.error(
            'Could not write file %s! Exception: %s', file_path, err_msg
        )
        return False


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
            if (data_from_file := load_file(self.file_name)) is None:
                logging.debug(
                    'Can\'t load data from file %s', self.file_name
                )
            else:
                logging.debug(
                    'Loaded data from file %s. %s keys.',
                    self.file_name, len(data_from_file.keys())
                )
                self.update(data_from_file)

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

    def pop(self, key) -> None:
        item = super().pop(key)

        logging.debug('DictFile %s popped.', self.file_name)

        save_file(self.file_name, self)

        return item
