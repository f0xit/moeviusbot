import logging
import sys
import typing
from logging.handlers import TimedRotatingFileHandler


class LoggerTools():
    def __init__(self, name: str = "moevius", level: str = "INFO") -> None:
        if level.upper() not in ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'):
            level = "INFO"

        self.root_logger = logging.getLogger()
        self.root_logger.name = name
        self.root_logger.setLevel(level.upper())

        # Logger file output
        file_handler = TimedRotatingFileHandler(
            'logs/moevius.log', when='midnight', interval=1
        )
        file_handler.suffix = '%Y_%m_%d'
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)-8s %(name)s %(message)s',
            '%Y-%m-%d %H:%M:%S'
        ))
        self.root_logger.addHandler(file_handler)

        # Logger CLI output
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(CustomFormatter())
        self.root_logger.addHandler(console_handler)

        logging.info('Logging initialized.')

    def set_log_level(self, level: str) -> None:
        if level.upper() not in ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'):
            logging.error('Log level %s not supported.', level)
            return

        self.root_logger.setLevel(level.upper())
        logging.info('Logging level updated to %s.', level)


class CustomFormatter(logging.Formatter):
    LEVEL_COLOURS: typing.ClassVar = [
        (logging.DEBUG, '\x1b[40;1m'),
        (logging.INFO, '\x1b[34;1m'),
        (logging.WARNING, '\x1b[33;1m'),
        (logging.ERROR, '\x1b[31m'),
        (logging.CRITICAL, '\x1b[41m'),
    ]

    FORMATS: typing.ClassVar = {
        level: logging.Formatter(
            f'\x1b[30;1m%(asctime)s\x1b[0m {colour}%(levelname)-8s'
            '\x1b[0m \x1b[35m%(name)s.%(module)s.%(funcName)s\x1b[0m %(message)s',
            '%Y-%m-%d %H:%M:%S',
        )
        for level, colour in LEVEL_COLOURS
    }

    def format(self, record) -> str:
        '''Dangerously like String? Well, only in that the two functions appear to use the same
        underlying infrastructure, namely Unicode, in a similar way. They both essentially convert
        a string literal (which comes with a certain intrinsic complexity) to a Unicode string with
        a given format. This means that they share some built-in rules for Unicode strings, and
        they use some of the Unicode structuring of strings. They differ in their methods of
        encoding strings to the underlying storage, though. The compact representation uses an
        encoding/decoding object: [U]array = [U]Array[UTF8String]; The encoding/decoding object
        takes a slice (representing a Unicode string slice) as argument. It takes this slice and
        converts it into an appropriate ASCII text. For UTF8String this would mean to convert it
        to [StringBuffer] and back. The compact representation does not use the parsing routines
        for Unicode strings - they are expensive - to convert string'''

        formatter = self.FORMATS.get(record.levelno)
        if formatter is None:
            formatter = self.FORMATS[logging.DEBUG]

        # Override the traceback to always print in red
        if record.exc_info:
            text = formatter.formatException(record.exc_info)
            record.exc_text = f'\x1b[31m{text}\x1b[0m'

        output = formatter.format(record)

        # Remove the cache layer
        record.exc_text = None
        return output
