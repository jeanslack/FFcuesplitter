"""
First release: January 16 2022

Name: main.py
Porpose: provides command line arguments for ffcuesplitter
Platform: all
Writer: jeanslack <jeanlucperni@gmail.com>
license: GPL3
Copyright: (C) 2023 Gianluca Pernigotto <jeanlucperni@gmail.com>
Rev: Jan 28 2022
Code checker: flake8, pylint
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
import argparse
from ffcuesplitter.info import (__appname__,
                                __description__,
                                __version__,
                                __release__,
                                )
from ffcuesplitter.str_utils import (msgdebug,
                                     msgend,
                                     msgcolor,
                                     )
from ffcuesplitter.user_service import (FileSystemOperations,
                                        FileFinder,
                                        )
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
    parser.add_argument('-i', '--input-fd',
                        metavar='FILENAMES DIRNAMES',
                        help=("It accepts both files and directories: Path "
                              "names can be absolute or relative; Multiple "
                              "path filenames or path dirnames must be "
                              "separated by one or more spaces between them. "
                              "See also recursive "
                              "mode (-r, --recursive)"),
                        nargs='+',
                        action="store",
                        required=True,
                        )
    parser.add_argument('-r', '--recursive',
                        action='store_true',
                        help=("Recursion flag to search sub-directories "
                              "under the given directories. Note that this "
                              "flag will only work with dirnames and will "
                              "have no effect with filenames."),
                        required=False,
                        )
    parser.add_argument('-f', '--format-type',
                        choices=["wav", "flac", "mp3", "ogg", "opus", "copy"],
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
                              "folder does not exist, it will be created. "
                              "If no outputdir option is specified, the "
                              "output files will be written to the default "
                              "output folder (the same as inputfile)."),
                        required=False,
                        default='.'
                        )
    parser.add_argument("-c", "--collection",
                        choices=["artist+album", "artist", "album"],
                        help=("Create additional subfolders in the output "
                              "destination (see --output-dir). The "
                              "`artist+album` argument "
                              "creates two subfolders with the artist and "
                              "album names; `artist` creates a subfolder with "
                              "the artist's name; `album` creates a subfolder "
                              "with the album name. In these subfolders the "
                              "final tracks will be saved."),
                        required=False,
                        default=''
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
                        metavar="'parameters'",
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
    parser.add_argument('--prg-loglevel',
                        help=("Set the program logging level of tracking "
                              "events to console, default is `info`"),
                        choices=["error", "warning", "info", "debug"],
                        required=False,
                        default='info'
                        )
    args = parser.parse_args()

    find = FileFinder(args.input_fd)  # get file collection
    if args.recursive is True:
        allfiles = find.find_files_recursively(suffix=('.cue', '.CUE'))

    elif args.recursive is False:
        allfiles = find.find_files(suffix=('.cue', '.CUE'))

    filelist = set(allfiles['FOUND']
                   + allfiles['DISCARDED']
                   + allfiles['INEXISTENT']
                   )
    if not filelist:
        msgdebug(err="No files found.")
        return None

    for files in filelist:
        kwargs = {'filename': files}
        kwargs['outputdir'] = args.outputdir
        kwargs['collection'] = args.collection
        kwargs['outputformat'] = args.format_type
        kwargs['overwrite'] = args.overwrite
        kwargs['ffmpeg_cmd'] = args.ffmpeg_cmd
        kwargs['ffmpeg_loglevel'] = args.ffmpeg_loglevel
        kwargs['ffmpeg_add_params'] = args.ffmpeg_add_params
        kwargs['ffprobe_cmd'] = args.ffprobe_cmd
        kwargs['progress_meter'] = args.progress_meter
        kwargs['dry'] = args.dry
        kwargs['prg_loglevel'] = args.prg_loglevel.upper()

        msgcolor(green='FFcuesplitter: ',
                 tail=f"Processing: '{kwargs['filename']}'")
        try:
            split = FileSystemOperations(**kwargs)
            if kwargs['dry']:
                split.dry_run_mode()
            else:
                overwr = split.check_for_overwriting()
                if not overwr:
                    split.work_on_temporary_directory()

        except (InvalidFileError,
                FFCueSplitterError,
                FFProbeError,
                FFMpegError,
                ) as error:
            msgdebug(err=f"{error}")
            return None

    msgend(done="Finished!")
    return None


if __name__ == '__main__':
    main()
