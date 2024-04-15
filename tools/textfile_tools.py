"""This tool contains functions to help reading text-files."""

from result import Err, Ok, Result


async def lines_from_textfile(filepath: str, /, encoding: str = "utf-8") -> Result[list[str], str]:
    """Returns a list of srings that represent the lines of a textfile."""

    try:
        with open(filepath, "r", encoding=encoding) as file:
            output: list[str] = file.readlines()
            return Ok(output)
    except OSError as err_msg:
        return Err(f"Failed reading file {filepath} with error: {err_msg}")


async def lines_to_textfile(filepath: str, lines: list[str], /, encoding: str = "utf-8") -> Result[str, str]:
    """Writes a list of strings as lines into a textfile."""

    try:
        with open(filepath, "w", encoding=encoding) as file:
            print(*lines, sep="\n", file=file)
            return Ok(f"Text file {filepath} written. {len(lines)} lines.")
    except OSError as err_msg:
        return Err(f"Failed reading file {filepath} with error: {err_msg}")
