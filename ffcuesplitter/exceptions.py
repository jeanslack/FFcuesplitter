"""
Name: exceptions.py
Porpose: defines class Exceptions for ffcuesplitter
Platform: MacOs, Gnu/Linux, FreeBSD
Writer: jeanslack <jeanlucperni@gmail.com>
license: GPL3
Rev: February 03 2022
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


class FFMpegError(Exception):
    """Excepion raised by FFMpeg class"""


class FFProbeError(Exception):
    """Excepion raised by FFProbe class"""


class InvalidFileError(Exception):
    """Exception type raised when CUE file is invalid."""


class FFCueSplitterError(Exception):
    """Exception raised in all other cases."""
