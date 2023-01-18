'''This tool contains functions to help loading/saving Python objects from/to .json-files'''

import json
import logging


def load_file(name: str) -> dict:
    '''Opens the file with the specified name and converts it to a dict.

    Important note: The file suffix is always .json, so the opened file for
    name = "example" would be "example.json".

    If the file could not be found or the name is empty, the function returns None.'''
    if str(name) == '':
        return None

    try:
        with open(f'{name}.json', 'r', encoding="utf-8") as file:
            return json.load(file)
    except OSError as err_msg:
        logging.error('Could not read file %s! Exception: %s', name, err_msg)
        return None


def save_file(name: str, content: dict) -> bool:
    '''Writes the content dict into a file with the specified name.

    Important note: The file suffix is always .json, so the opened file for
    name = "example" would be "example.json".

    If the file could not be found or the name is empty, the function returns False,
    otherwise it returns True.'''
    if str(name) == '':
        return False

    try:
        with open(f'{name}.json', 'w', encoding="utf-8") as file:
            json.dump(content, file)
            return True
    except OSError as err_msg:
        logging.error('Could not write file %s! Exception: %s', name, err_msg)
        return False
