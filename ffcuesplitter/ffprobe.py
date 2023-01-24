# -*- coding: UTF-8 -*-
"""
Name: ffprobe.py
Porpose: simple cross-platform wrap for ffprobe
Compatibility: Python3
Platform: all
Author: Gianluca Pernigotto <jeanlucperni@gmail.com>
Copyright: (C) 2023 Gianluca Pernigotto <jeanlucperni@gmail.com>
license: GPL3
Rev: Dec.14.2022
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
from ffcuesplitter.exceptions import FFProbeError
from ffcuesplitter.utils import Popen


def from_kwargs_to_args(kwargs):
    """
    Helper function to build command line
    arguments out of dict.
    """
    args = []
    for key in sorted(kwargs.keys()):
        val = kwargs[key]
        args.append(f'-{key}')
        if val is not None:
            args.append(f'{val}')
    return args


def ffprobe(filename, cmd='ffprobe', **kwargs):
    """
    Run ffprobe subprocess on the specified file.

    Raises:
        `FFProbeError` from `FileNotFoundError` or from `OSError`.
        `FFProbeError` if non-zero exit code from `proc.returncode`.
    Return:
        A JSON representation of the ffprobe output.
    Usage:
        >>> from ffcuesplitter.ffprobe import ffprobe
        >>> probe = ffprobe(filename,
                            cmd='/usr/bin/ffprobe',
                            loglevel='error',
                            hide_banner=None,
                            kwargs,
                            )

    """
    args = (f'"{cmd}" -show_format -show_streams -of json '
            f'{" ".join(from_kwargs_to_args(kwargs))} '
            f'"{filename}"'
            )
    args = shlex.split(args) if platform.system() != 'Windows' else args

    try:
        with Popen(args,
                   stdout=subprocess.PIPE,
                   stderr=subprocess.PIPE,
                   universal_newlines=True,
                   encoding='utf8',
                   ) as proc:
            output, error = proc.communicate()

            if proc.returncode != 0:
                raise FFProbeError(f'ffprobe: {error}')

    except (OSError, FileNotFoundError) as excepterr:
        raise FFProbeError(excepterr) from excepterr

    else:
        return json.loads(output)
