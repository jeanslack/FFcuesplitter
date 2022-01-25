"""
Name: utils.py
Porpose: utils used by FFcuesplitter
Platform: MacOs, Gnu/Linux, FreeBSD
Writer: jeanslack <jeanlucperni@gmail.com>
license: GPL3
Rev: January 16 2022
Code checker: flake8 and pylint
####################################################################

This file is part of ffcuesplitter.

    ffcuesplitter is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    ffcuesplitter is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with ffcuesplitter.  If not, see <http://www.gnu.org/licenses/>.
"""
import subprocess
import platform
import datetime


def pairwise(iterable):
    """
    Return a zip object from iterable.
    This function is used by run method.
    ----
    USE:

    after splitting ffmpeg's progress strings such as:
    output = "frame= 1178 fps=155 q=29.0 size=    2072kB time=00:00:39.02
              bitrate= 435.0kbits/s speed=5.15x  "
    in a list as:
    iterable = ['frame', '1178', 'fps', '155', 'q', '29.0', 'size', '2072kB',
                'time', '00:00:39.02', 'bitrate', '435.0kbits/s', speed',
                '5.15x']
    for x, y in pairwise(iterable):
        (x,y)

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
