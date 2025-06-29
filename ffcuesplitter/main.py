"""
First release: January 16 2022

Name: main.py
Porpose: provides command line arguments for ffcuesplitter
Platform: all
Writer: jeanslack <jeanlucperni@gmail.com>
license: GPL3
Copyleft: (C) 2025 Gianluca Pernigotto <jeanlucperni@gmail.com>
Rev: June 10 2025
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
from ffcuesplitter.about import (APPNAME,
                                 SHORT_DESCRIPT,
                                 VERSION,
                                 RELEASE
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
                                      ParserError,
                                      )


def main():
    """
    Defines and evaluates positional arguments
    using the argparser module.
    """
    parser = argparse.ArgumentParser(prog=APPNAME,
                                     description=SHORT_DESCRIPT,
                                     # add_help=False,
                                     )
    parser.add_argument('--version',
                        help="Show the current version and exit.",
                        action='version',
                        version=(f"ffcuesplitter v{VERSION} "
                                 f"- {RELEASE}"),
                        )
    parser.add_argument('-i', '--input-fd',
                        metavar='FILENAMES DIRNAMES',
                        help=("It accepts both files and directories: Path "
                              "names can be absolute or relative; Multiple "
                              "path filenames or path dirnames must be "
                              "separated by one or more spaces between them. "
                              "See also recursive "
                              "option (-r, --recursive)"),
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
    parser.add_argument('-f', '--output-format',
                        choices=["wav", "flac", "mp3", "ogg", "opus"],
                        help=("Preferred audio format to output, "
                              "default is 'flac'."),
                        required=False,
                        default='flac',
                        )
    parser.add_argument("-o", "--output-dir",
                        action="store",
                        dest="outputdir",
                        help=("Absolute or relative destination path for "
                              "output files. Default is '.', the same as "
                              "inputfile."),
                        required=False,
                        default='.'
                        )
    parser.add_argument("-del", "--del-orig-files",
                        action='store_true',
                        help=("Remove original files after successfull "
                              "conversion. Please note that the audio file "
                              "and CUE file will be permanently deleted from "
                              "your filesystem, do this at your own risk."),
                        required=False,
                        )
    parser.add_argument("-c", "--collection",
                        choices=["author+album", "author", "album"],
                        help=("Create additional sub-dirctories for audio "
                              "collection."),
                        required=False,
                        default=''
                        )
    parser.add_argument("-ow", "--overwrite",
                        choices=["ask", "never", "always"],
                        dest="overwrite",
                        help=("Preferences on overwriting files in the "
                              "destination path. Default is `ask` before "
                              "overwriting."),
                        required=False,
                        default='ask'
                        )
    parser.add_argument("-ce", "--characters-encoding",
                        action="store",
                        help=("Specify a custom character encoding, in case "
                              "the automatic one fails. The default is "
                              "«auto»"),
                        required=False,
                        default='auto'
                        )
    parser.add_argument("--ffmpeg-cmd",
                        metavar='URL',
                        help=("Specify an absolute ffmpeg path command, "
                              "e.g. '/usr/bin/ffmpeg'. Default is `ffmpeg`."),
                        required=False,
                        default='ffmpeg'
                        )
    parser.add_argument("--ffmpeg-loglevel",
                        choices=["error", "warning", "info",
                                 "verbose", "debug"],
                        help=("ffmpeg loglevel. Default is `info`."),
                        required=False,
                        default='info'
                        )
    parser.add_argument("--ffmpeg-add-params",
                        metavar="parameters",
                        help=("Additionals ffmpeg parameters. Note that the "
                              "additional parameters must be quoted using "
                              "single quotes and must be preceded by an "
                              "equals sign (=), example: "
                              "--ffmpeg-add-params='-c:a flac -ar 44100'."),
                        required=False,
                        default=''
                        )
    parser.add_argument("-p", "--progress-meter",
                        help=("Progress bar mode. Default is `tqdm`."),
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

    find = FileFinder(args.input_fd)  # get all cue files
    if args.recursive is True:
        allfiles = find.find_files_recursively(suffix=('.cue', '.CUE'))
    else:
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
        kwargs['outputformat'] = args.output_format
        kwargs['overwrite'] = args.overwrite
        kwargs['characters_encoding'] = args.characters_encoding.strip()
        kwargs['del_orig_files'] = args.del_orig_files
        kwargs['ffmpeg_cmd'] = args.ffmpeg_cmd
        kwargs['ffmpeg_loglevel'] = args.ffmpeg_loglevel
        kwargs['ffmpeg_add_params'] = args.ffmpeg_add_params
        kwargs['ffprobe_cmd'] = args.ffprobe_cmd
        kwargs['progress_meter'] = args.progress_meter
        kwargs['dry'] = args.dry
        kwargs['prg_loglevel'] = args.prg_loglevel.upper()
        kwargs['testpatch'] = False

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
                ParserError,
                ) as error:
            msgdebug(err=f"{error}")
            return None

    msgend(done="Finished!")
    return None


if __name__ == '__main__':
    main()
