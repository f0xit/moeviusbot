"""This tool contains functions to help reading text-files."""

import logging


async def lines_from_textfile(filepath: str, /, encoding: str = "utf-8") -> list[str]:
    """Returns a list of srings that represent the lines of a textfile."""

    try:
        with open(filepath, "r", encoding=encoding) as file:
            output = [clean_line for line in file.readlines() if (clean_line := line.strip())]
            logging.debug("Read file %s with %s lines.", filepath, len(output))
            return output
    except OSError as err_msg:
        logging.error("Could not read file %s! Error: %s", filepath, err_msg)
        return output


async def lines_to_textfile(filepath: str, lines: list[str], /, encoding: str = "utf-8") -> None:
    """Writes a list of strings as lines into a textfile."""

    try:
        with open(filepath, "w", encoding=encoding) as file:
            print(*lines, sep="\n", file=file)
            logging.debug("Text file %s written with %s lines.", filepath, len(lines))
    except OSError as err_msg:
        logging.error("Could not write file %s! Error: %s", filepath, err_msg)
