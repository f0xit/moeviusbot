import io
import random

SUBSTITUTE = {
    "q": ["w", "a"],
    "w": ["e", "s", "a", "q"],
    "e": ["r", "d", "s", "w"],
    "r": ["t", "f", "d", "e"],
    "t": ["z", "g", "f", "e"],
    "z": ["u", "h", "g", "t"],
    "u": ["i", "j", "h", "z"],
    "i": ["o", "k", "j", "u"],
    "o": ["p", "l", "k", "i"],
    "p": ["ü", "ö", "l", "o"],
    "ü": ["ä", "ö", "p"],
    "a": ["q", "w", "s", "y"],
    "s": ["w", "e", "d", "x", "y", "a"],
    "d": ["e", "r", "f", "c", "x", "s"],
    "f": ["r", "t", "g", "v", "c", "d"],
    "g": ["t", "z", "h", "b", "v", "f"],
    "h": ["z", "u", "j", "n", "b", "g"],
    "j": ["u", "i", "k", "m", "n", "h"],
    "k": ["i", "o", "l", "m", "j"],
    "l": ["o", "p", "ö", "k"],
    "ö": ["p", "ü", "ä", "l"],
    "ä": ["ü", "ö"],
    "y": ["a", "s", "x"],
    "x": ["s", "d", "c", "y"],
    "c": ["d", "f", "v", "x"],
    "v": ["f", "g", "b", "c"],
    "b": ["g", "h", "n", "v"],
    "n": ["h", "j", "m", "b"],
    "m": ["j", "k", "n"],
    " ": ["c", "v", "b", "n", "m"],
}


def schnenkify(message: str, percent: int = 5) -> str:
    with io.StringIO() as output:
        for character in message:
            char = character
            if char.isdecimal():
                output.write(char)
                continue

            try:
                if random.SystemRandom().randint(1, round(100 / max(min(percent, 100), 1))) == 1:
                    uppercase = char.isupper()
                    char = random.SystemRandom().choice(SUBSTITUTE[char.lower()])
                    if uppercase:
                        char = char.upper()
            except KeyError:
                pass
            finally:
                output.write(char)

        return output.getvalue()
