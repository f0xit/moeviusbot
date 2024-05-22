from string import ascii_lowercase


def convert_choices_to_list(choices_str: str) -> list[tuple[str, str]]:
    """Takes a string, splits it by semicolons, and turns the chunks into
    a list, enumerated by lowercase letters, starting at 'a'.

    Trailing semicolons or whitespace between semicolons are ignored.

    Example:
        'apple; banana ; ;cake;' is converted into
        [('a', 'apple'),('b', 'banana'),('c', 'cake')]

    Args:
        choices_str (str): A string of choices, seperated by semicolons

    Returns:
        list[tuple[str, str]]: A list of choices, enumerated by lowercase
        letters, starting at 'a'"""

    return list(zip(ascii_lowercase, [name for name in map(str.strip, choices_str.split(";")) if name]))

