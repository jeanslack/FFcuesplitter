# -*- coding: utf-8 -*-
"""
Name: str_utils.py (module)
Porpose: module for cosmetic output console in ANSI sequences
Writer: Gianluca Pernigoto <jeanlucperni@gmail.com>
Copyright: (C) 2023 Gianluca Pernigotto <jeanlucperni@gmail.com>
license: GPL3
Rev: Jan 29 2023
Code checker: flake8, pylint
"""


def msgdebug(head='', info=None, warn=None, err=None, tail=''):
    """
    Print debug messages:
    ``head`` can be used for additionals custom string to use
             at the beginning of the string.
    ``tail`` can be used for additionals custom string to use
             at the end of the string.
     ``info`` print in blue color, ``warn`` print in yellow color
     ``err`` print in red color.
    """
    if info:
        print(f"{head}\033[32;1mINFO:\033[0m {info}{tail}")
    elif warn:
        print(f"{head}\033[33;1mWARNING:\033[0m {warn}{tail}")
    elif err:
        print(f"{head}\033[31;1mERROR:\033[0m {err}{tail}")


def msgcolor(head='', orange=None, green=None, azure=None, tail=''):
    """
    Print information messages by explicitly
    choosing the name of the color to be displayed:
    ``head`` can be used for additionals custom string to use
             at the beginning of the string.
    ``tail`` can be used for additionals custom string to use
             at the end of the string.
    """
    if orange:
        print(f"{head}\033[33;1m{orange}\033[0m{tail}")

    elif green:
        print(f"{head}\033[32;1m{green}\033[0m{tail}")

    elif azure:
        print(f"{head}\033[34;1m{azure}\033[0m{tail}")


def msgend(done=None, abort=None):
    """
    Print status messages at the end of the tasks
    """
    if done:
        print("\033[32;1mFinished!\033[0m\n")
    elif abort:
        print("\033[31;1mAbort!\033[0m\n")


def msg(message):
    """
    Print any string messages
    """
    print(message)
