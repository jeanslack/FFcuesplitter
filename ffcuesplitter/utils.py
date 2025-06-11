"""
Name: utils.py
Porpose: utils used by FFcuesplitter
Platform: all
Writer: jeanslack <jeanlucperni@gmail.com>
license: GPL3
Copyleft: (C) 2025 Gianluca Pernigotto <jeanlucperni@gmail.com>
Rev: June 10 2025
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


def sanitize(string: str = 'string') -> str:
    r"""
    Makes the passed string consistent and compatible with most
    popular operating system file systems.

    - Replaces slash (/) character with hyphen (-) .
    - Removes several meta-characters that may be incompatible
      with filesystems .
    - Normalizes all spaces and tabs along the string.

    Returns the new sanitized string.

    """
    if not isinstance(string, str):
        raise TypeError("Expects Type string only")

    string = string.replace('/', '-')
    string = re.sub(r"[\.\'\^\`\~\"\#\'\%\&\*\:\<\>\?\/\\\{\|\}]", '', string)

    return " ".join(string.split())  # normalizing all spaces
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


def makeoutputdirs(outputdir):
    """
    Makes the specified sub-dirctories in the outputdir
    """
    try:
        os.makedirs(outputdir,
                    mode=0o777,
                    exist_ok=True
                    )
    except Exception as error:
        raise ValueError(error) from error
# ------------------------------------------------------------------------


class Popen(subprocess.Popen):
    """
    Inherit `subprocess.Popen` class to set `_startupinfo`.
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
