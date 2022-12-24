"""
Name: utils.py
Porpose: utils used by FFcuesplitter
Platform: all
Writer: jeanslack <jeanlucperni@gmail.com>
license: GPL3
Rev: Dec 20 2022
Code checker: flake8 and pylint
####################################################################

This file is part of FFcuesplitter.

    FFcuesplitter is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    FFcuesplitter is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with FFcuesplitter.  If not, see <http://www.gnu.org/licenses/>.
"""
import os
import re
import subprocess
import platform
import datetime


def file_cataloger(target: str = 'pathdir or list of',
                   suffix: str = '.suffix or list of',
                   recursive: bool = False) -> dict:
    """
    Searches and catalogs file types with a given suffixes
    whitin a list of directories. Accepts a string or a list
    of one or more directories, a string or a list of one or
    more suffixes to search for, and a boolean parameter for
    recursive mode.
    If files instead of directories are passed, they are
    rejected by default but still returned in a `rejected`
    list. Non-existent files and directories are not processed
    at all.
    Always returns a dictionary with two keys: `FILTERED` and `REJECTED`
    and lists as values.
    Assert

    """
    target = tuple((target,)) if isinstance(target, str) else target
    suffix = tuple((suffix,)) if isinstance(suffix, str) else suffix
    fileswalk = {}
    onlydirs = []
    filtered = []
    rejected = []  # add here if it's file

    for f_or_d in target:
        if os.path.exists(f_or_d):
            if os.path.isdir(f_or_d):
                onlydirs.append(f_or_d)
            else:
                rejected.append(f_or_d)  # files only

    for dirs in onlydirs:
        if recursive is True:
            for root, _, files in os.walk(dirs):
                fileswalk[root] = list(files)

            for path, name in fileswalk.items():
                for ext in name:
                    if os.path.splitext(ext)[1] in suffix:
                        found = os.path.join(path, ext)
                        if found not in filtered:
                            filtered.append(found)
        else:
            for ext in os.listdir(dirs):
                if os.path.splitext(ext)[1] in suffix:
                    found = os.path.join(dirs, ext)
                    if found not in filtered:
                        filtered.append(found)

    return dict(FILTERED=filtered, REJECTED=rejected)
# ------------------------------------------------------------------------


def sanitize(string: str = 'stringa') -> str:
    r"""
    Makes the passed string consistent and compatible
    with file systems of some operating systems.

    All OS:
    Remove all leading/trailing spaces and dots.

    On Windows it removes the following illegal chars: " * : < > ? / \ |
    On Unix it remove slash char: /
    Returns the new sanitized string

    """
    msg = f"Only accepts <class 'str'> not {type(string)}"
    assert isinstance(string, str), msg
    newstr = string.strip().strip('.')  # spaces and dots

    if platform.system() == 'Windows':
        return re.sub(r"[\"\*\:\<\>\?\/\|\\]", '', newstr)

    return newstr.replace('/', '')
# ------------------------------------------------------------------------


def pairwise(iterable):
    """
    Return a zip object from iterable.
    This function is used by run method.
    ----
    USAGE:

    after splitting ffmpeg's progress strings such as:
    >>> output = ("frame= 1178 fps=155 q=29.0 size=    2072kB "
                  "time=00:00:39.02 bitrate= 435.0kbits/s speed=5.15x  ")
    in a list as:

    >>> iterable = [a for a in "=".join(output.split()).split('=') if a]
    >>> iterable  # get list like this:
    >>> ['frame', '1178', 'fps', '155', 'q', '29.0', 'size', '2072kB',
         'time', '00:00:39.02', 'bitrate', '435.0kbits/s', speed',
         '5.15x']

    >>> for x, y in pairwise(iterable):
            x,y

    <https://stackoverflow.com/questions/5389507/iterating-over-every-
    two-elements-in-a-list>

    """
    itobj = iter(iterable)  # list_iterator object
    return zip(itobj, itobj)  # zip object pairs from list iterable object
# ------------------------------------------------------------------------


def frames_to_seconds(frames):
    """
    Converts frames (10407600) to seconds (236.0) and then
    converts them to a time format string (0:03:56) using datetime.
    """
    secs = frames / 44100
    return str(datetime.timedelta(seconds=secs))
# ------------------------------------------------------------------------


class Popen(subprocess.Popen):
    """
    Inherit subprocess.Popen class to set _startupinfo.
    This avoids displaying a console window on MS-Windows
    using GUI's .
    """
    if platform.system() == 'Windows':
        _startupinfo = subprocess.STARTUPINFO()
        _startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    else:
        _startupinfo = None

    def __init__(self, *args, **kwargs):
        """Constructor
        """
        super().__init__(*args, **kwargs, startupinfo=self._startupinfo)

    # def communicate_or_kill(self, *args, **kwargs):
        # return process_communicate_or_kill(self, *args, **kwargs)
# ------------------------------------------------------------------------
