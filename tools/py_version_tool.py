import sys


def check_python_version() -> bool:
    major_version, minor_version, micro_version, _, _ = sys.version_info
    if (major_version, minor_version) < (3, 11):
        sys.exit('Wrong Python version. Please use at least 3.11.')
