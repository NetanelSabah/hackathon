import random

DEBUG = False
LOW_DEBUG = DEBUG and True

def log(st):
    if DEBUG:
        print(bcolors.GREEN + st + bcolors.WHITE)

def lowLog(st):
    if LOW_DEBUG:
        print(bcolors.DARK_GREEN + st + bcolors.WHITE)

def err(st):
    if DEBUG:
        print(bcolors.RED + st + bcolors.WHITE)

def colorName(st):
    return chooseColor(st) + st + bcolors.WHITE

def chooseColor(st):
    return bcolors.COLORS_POOL[sum(map(ord, st)) % len(bcolors.COLORS_POOL)]

class bcolors:
    RED = '\u001b[31m'  # only for errors
    DARK_RED = '\u001b[38;5;$88m'
    DARK_GREEN = '\u001b[38;5;$22m'  # lowLog
    GREEN = '\u001b[32m'  # log
    YELLOW = '\u001b[33m'
    BLUE = '\u001b[34m'
    MAGENTA = '\u001b[35m'
    CYAN = '\u001b[36m'
    BRIGHT_RED = '\u001b[31;1m'
    BRIGHT_GREEN = '\u001b[32;1m'
    BRIGHT_YELLOW = '\u001b[33;1m'
    BRIGHT_BLUE = '\u001b[34;1m'
    BRIGHT_MAGENTA = '\u001b[35;1m'
    BRIGHT_CYAN = '\u001b[36;1m'
    WHITE = '\u001b[37m'  # normal text

    COLORS_POOL = [DARK_RED, YELLOW, BLUE, MAGENTA, CYAN, BRIGHT_RED, BRIGHT_GREEN, BRIGHT_YELLOW, BRIGHT_BLUE, BRIGHT_MAGENTA, BRIGHT_CYAN]