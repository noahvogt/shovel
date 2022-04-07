import sys

from termcolor import colored

def error_exit(message: str, exit_code=1):
    print(colored("[*] Error: {}".format(message), "red"))
    sys.exit(exit_code)


def msg(message: str, severity="normal"):
    severity_colors = {"normal": "white", "success": "green", "error": "red",
                       "action": "cyan", "warning": "yellow"}
    print(colored("[*] {}".format(message), severity_colors.get(severity)))
