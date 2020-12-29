import random

DEBUG = True

def log(st):
    if DEBUG:
        print(bcolors.GREEN + st + bcolors.WHITE)

def err(st):
    if DEBUG:
        print(bcolors.RED + st + bcolors.WHITE)

def colorName(st):
    return random.choice(bcolors.COLORS_POOL) + st + bcolors.WHITE

class bcolors:
    RED = '\u001b[31m'
    GREEN = '\u001b[32m'
    YELLOW = '\u001b[33m'
    BLUE = '\u001b[34m'
    MAGENTA = '\u001b[35m'
    CYAN = '\u001b[36m'
    WHITE = '\u001b[37m'

    COLORS_POOL = [YELLOW, BLUE, MAGENTA, CYAN]