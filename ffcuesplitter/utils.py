"""
Name: utils.py
Porpose: utils used by FFcuesplitter
Platform: all
Writer: jeanslack <jeanlucperni@gmail.com>
license: GPL3
Rev: Dec 27 2022
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


def makeoutputdirs(outputdir):
    """
    Makes the subfolders specified in the outpudir argument
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


class FileFinder:
    """
    Finds and collect files based on one or more suffixes in
    a given pathnames list. Features methods for recursive and
    non-recursive searching.

    Constructor:

        ff = FileFinder(target=str('pathnames'))
        or
        ff = FileFinder(target=list('pathnames',))

    Available methods:

        - find_files(suffix=str or list of ('.suffix',))
        - find_files_recursively(suffix=str or list of ('.suffix',))

    Always returns a dictionary with three keys:
    `FOUND`, `DISCARDED`, `INEXISTENT` with lists as values.

    If filenames are given instead of dirnames, they will be
    returned with the `DISCARDED` key. If non-existent filenames
    or dirnames are given, they will be returned with the
    `INEXISTENT` key. All files found will be returned with
    the FOUND key.

    """
    def __init__(self, target: str = ''):
        """
        target: Expects a str('pathdir') or a list of ('pathdirs',)

        """
        self.filtered = None
        self.rejected = None  # add here only if it's file
        self.nonexistent = None
        self.target = tuple((target,)) if isinstance(target, str) else target
    # -------------------------------------------------------------#

    def find_files_recursively(self, suffix: str = '') -> dict:
        """
        find files in recursive mode.
        suffix: Expects a str(.suffix) or a list of (.suffixes,)
        Returns: dict

        """
        self.filtered = []
        self.rejected = []  # add here only if it's file
        self.nonexistent = []
        suffix = tuple((suffix,)) if isinstance(suffix, str) else suffix

        fileswalk = {}
        for dirs in self.target:
            if os.path.exists(dirs):
                if os.path.isdir(dirs):
                    for root, alldirs, allfiles in os.walk(dirs):
                        # to disable some `for` variables put underscore _
                        fileswalk[root] = list(alldirs + allfiles)
                else:
                    self.rejected.append(dirs)  # only existing files
            else:
                self.nonexistent.append(dirs)  # all non-existing files/dirs
        for path, name in fileswalk.items():
            for files in name:
                if os.path.splitext(files)[1] in suffix:
                    self.filtered.append(os.path.join(path, files))

        return dict(FOUND=self.filtered,
                    DISCARDED=self.rejected,
                    INEXISTENT=self.nonexistent
                    )
    # -------------------------------------------------------------#

    def find_files(self, suffix: str = '') -> dict:
        """
        find files in non-recursive mode.
        suffix: Expects a str(.suffix) or a list of (.suffixes,)
        Returns: dict

        """
        self.filtered = []
        self.rejected = []  # add here only if it's file
        self.nonexistent = []
        suffix = tuple((suffix,)) if isinstance(suffix, str) else suffix

        for dirs in self.target:
            if os.path.exists(dirs):
                if os.path.isdir(dirs):
                    for files in os.listdir(dirs):
                        if os.path.splitext(files)[1] in suffix:
                            self.filtered.append(os.path.join(dirs, files))
                else:
                    self.rejected.append(dirs)  # only existing files
            else:
                self.nonexistent.append(dirs)  # all non-existing files/dirs

        return dict(FOUND=self.filtered,
                    DISCARDED=self.rejected,
                    INEXISTENT=self.nonexistent
                    )
# ------------------------------------------------------------------------
