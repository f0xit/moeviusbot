'''Checks the python version'''
import sys


def check_python_version(
    min_major_version: int = 3,
    min_minor_version: int = 11,
) -> None:
    '''Exits the script if version is below '''
    major_version, minor_version, _, _, _ = sys.version_info
    if (major_version, minor_version) < (min_major_version, min_minor_version):
        sys.exit(
            f'Wrong Python version. Please use at least {min_major_version,}.{min_minor_version}!'
        )
