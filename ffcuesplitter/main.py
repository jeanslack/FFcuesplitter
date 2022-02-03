"""
First release: January 16 2022

Name: main.py
Porpose: provides command line arguments for ffcuesplitter
Platform: MacOs, Gnu/Linux, FreeBSD
Writer: jeanslack <jeanlucperni@gmail.com>
license: GPL3
Rev: February 03 2022
Code checker: flake8, pylint
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
import argparse

from ffcuesplitter.info import (__appname__,
                                __description__,
                                __version__,
                                __release__
                                )
from ffcuesplitter.cuesplitter import FFCueSplitter
from ffcuesplitter.str_utils import msgdebug
from ffcuesplitter.exceptions import (InvalidFileError,
                                      FFCueSplitterError,
                                      FFProbeError,
                                      FFMpegError,
                                      )



def main():
    """
    Defines and evaluates positional arguments
    using the argparser module.
    """
    parser = argparse.ArgumentParser(prog=__appname__,
                                     description=__description__,
                                     # add_help=False,
                                     )
    parser.add_argument('--version',
                        help="Show the current version and exit.",
                        action='version',
                        version=(f"ffcuesplitter v{__version__} "
                                 f"- {__release__}"),
                        )
    parser.add_argument('-i', '--input-cuefile',
                        metavar='IMPUTFILE',
                        help=("An absolute or relative CUE sheet file, "
                              "example: -i 'mycuesheetfile.cue'."),
                        action="store",
                        required=False,
                        )
    parser.add_argument('-f', '--format-type',
                        choices=["wav", "flac", "mp3", "ogg", "copy"],
                        help=("Preferred audio format to output, "
                              "default is 'flac'."),
                        required=False,
                        default='flac',
                        )
    parser.add_argument("-o", "--output-dir",
                        action="store",
                        dest="outputdir",
                        help=("Absolute or relative destination path for "
                              "output files. If a specified destination "
                              "folder does not exist, it will be created "
                              "automatically. By default it is the same "
                              "path location as IMPUTFILE."),
                        required=False,
                        default='.'
                        )
    parser.add_argument("-ow", "--overwrite",
                        choices=["ask", "never", "always"],
                        dest="overwrite",
                        help=("Overwrite files on destination if they "
                              "exist, Default is `ask` before overwriting."),
                        required=False,
                        default='ask'
                        )
    parser.add_argument("--ffmpeg-cmd",
                        metavar='URL',
                        help=("Specify an absolute ffmpeg path command, "
                              "e.g. '/usr/bin/ffmpeg', Default is `ffmpeg`."),
                        required=False,
                        default='ffmpeg'
                        )
    parser.add_argument("--ffmpeg-loglevel",
                        choices=["error", "warning", "info",
                                 "verbose", "debug"],
                        help=("Specify a ffmpeg loglevel, "
                              "Default is `info`."),
                        required=False,
                        default='info'
                        )
    parser.add_argument("--ffmpeg-add-params",
                        metavar="'PARAMS ...'",
                        help=("Additionals ffmpeg parameters, as 'codec "
                              "quality', etc. Note, all additional "
                              "parameters must be quoted."),
                        required=False,
                        default=''
                        )
    parser.add_argument("-p", "--progress-meter",
                        help=("Progress bar mode. This takes effect during "
                              "FFmpeg process loops. Default is `tqdm`."),
                        choices=["tqdm", "standard"],
                        required=False,
                        default='tqdm'
                        )
    parser.add_argument("--ffprobe-cmd",
                        metavar='URL',
                        help=("Specify an absolute ffprobe path command, e.g. "
                              "'/usr/bin/ffprobe', Default is `ffprobe`."),
                        required=False,
                        default='ffprobe'
                        )
    parser.add_argument("--dry",
                        action='store_true',
                        help=("Perform the dry run with no changes done to "
                              "filesystem. Only show what would be done."),
                        required=False,
                        )
    args = parser.parse_args()

    if args.input_cuefile:
        kwargs = {'filename': args.input_cuefile}
        kwargs['outputdir'] = args.outputdir
        kwargs['suffix'] = args.format_type
        kwargs['overwrite'] = args.overwrite
        kwargs['ffmpeg_cmd'] = args.ffmpeg_cmd
        kwargs['ffmpeg_loglevel'] = args.ffmpeg_loglevel
        kwargs['ffmpeg_add_params'] = args.ffmpeg_add_params
        kwargs['ffprobe_cmd'] = args.ffprobe_cmd
        kwargs['progress_meter'] = args.progress_meter
        kwargs['dry'] = args.dry

        try:
            split = FFCueSplitter(**kwargs)
            split.open_cuefile()
            split.do_operations()

        except (InvalidFileError,
                FFCueSplitterError,
                FFProbeError,
                FFMpegError) as error:
            msgdebug(err=f"{error}")
        else:
            msgdebug(info="Finished!")
    else:
        parser.error("Requires an INPUTFILE, please provide it")


if __name__ == '__main__':
    main()
