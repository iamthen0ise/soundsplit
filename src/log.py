import logging
import sys


class Color:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


LOGGING_FMT = f"{Color.BLUE} %(asctime)s | %(name)s | %(levelname)s {Color.ENDC} | {Color.GREEN} %(message)s {Color.ENDC}"
