# -*- coding: UTF-8 -*-
"""
Name: ffprobe.py
Porpose: simple cross-platform wrap for ffprobe
Compatibility: Python3
Platform: all
Author: Gianluca Pernigotto <jeanlucperni@gmail.com>
Copyleft: (C) 2025 Gianluca Pernigotto <jeanlucperni@gmail.com>
license: GPL3
Rev: June 10 2025
Code checker: flake8, pylint
########################################################

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
import subprocess
import shlex
import platform
import json
from ffcuesplitter.utils import Popen
from ffcuesplitter.exceptions import FFProbeError


def ffprobe(filename, cmd='ffprobe'):
    """
    Run ffprobe subprocess on the specified file.

    Raises:
        `FFProbeError` from `FileNotFoundError` or from `OSError`.
        `FFProbeError` if `error` from `proc.communicate`.
        `FFProbeError` if the given file is invalid.
    Return:
        A JSON representation of the ffprobe output.
    Usage:
        >>> from ffcuesplitter.ffprobe import ffprobe
        >>> probe = ffprobe(filename, cmd='/usr/bin/ffprobe')
    """
    args = (f'"{cmd}" -show_format -show_streams -of json '
            f'-loglevel error -hide_banner "{filename}"'
            )
    args = shlex.split(args) if platform.system() != 'Windows' else args
    output = None
    unchunkable = 'Invalid or non-splittable source file'

    try:
        with Popen(args,
                   stdout=subprocess.PIPE,
                   stderr=subprocess.PIPE,
                   universal_newlines=True,
                   bufsize=1,
                   encoding='utf8',
                   ) as proc:
            output, error = proc.communicate()

            if error:
                raise FFProbeError(f'ffprobe: {error}')

    except (OSError, FileNotFoundError) as excepterr:
        raise FFProbeError(excepterr) from excepterr

    if output:
        output = json.loads(output)
        if output['format'].get('duration'):
            dur = output['format'].get('duration')
            if int(float(dur)) == 0:
                raise FFProbeError(f'"{filename}"\nffprobe: {unchunkable}')
        else:
            raise FFProbeError(f'"{filename}"\nffprobe: {unchunkable}')
    else:
        raise FFProbeError(f'"{filename}"\nffprobe: {unchunkable}')

    return output
