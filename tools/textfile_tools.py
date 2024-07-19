"""This tool contains functions to help reading text-files."""

from __future__ import annotations

import logging
from pathlib import Path


async def lines_from_textfile(filepath: str, /, encoding: str = "utf-8") -> list[str]:
    """Returns a list of srings that represent the lines of a textfile."""

    try:
        with Path(filepath).open("r", encoding=encoding) as file:  # noqa: ASYNC230
            output = [clean_line for line in file if (clean_line := line.strip())]
            logging.debug("Read file %s with %s lines.", filepath, len(output))
            return output
    except OSError:
        logging.exception("Could not read file %s!", filepath)
        return output


async def lines_to_textfile(filepath: str, lines: list[str], /, encoding: str = "utf-8") -> None:
    """Writes a list of strings as lines into a textfile."""

    try:
        with Path(filepath).open("w", encoding=encoding) as file:  # noqa: ASYNC230
            print(*lines, sep="\n", file=file)
            logging.debug("Text file %s written with %s lines.", filepath, len(lines))
    except OSError:
        logging.exception("Could not write file %s!", filepath)
