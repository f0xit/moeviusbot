'''This tool contains functions to help reading text-files.'''

import logging


def lines_from_textfile(filepath: str, /, encoding: str = 'utf-8') -> list[str] | None:
    """Returns a list of srings that represent the lines of a textfile.

    Args:
        filepath (str): The path to the file
        encoding (str, optional): The file's encoding. Defaults to 'utf-8'.

    Returns:
        list[str] | None: A list with strings, representing each line of the read file.
    """
    try:
        with open(filepath, 'r', encoding=encoding) as file:
            output: list[str] = file.readlines()
            logging.debug(
                'Text file %s read. %s lines.',
                filepath, len(output)
            )
            return output
    except OSError as err_msg:
        logging.error(
            'Failed reading file %s with error: %s',
            filepath, err_msg
        )
        return None


def lines_to_textfile(filepath: str, lines: list[str], /, encoding: str = 'utf-8') -> None:
    """_summary_

    Args:
        filepath (str): _description_
        lines (list[str]): _description_
        encoding (str, optional): _description_. Defaults to 'utf-8'.
    """
    with open(filepath, 'w', encoding=encoding) as file:
        print(*lines, sep='\n', file=file)
