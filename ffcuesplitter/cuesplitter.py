"""
First release: January 16 2022

Name: cuesplitter.py
Porpose: FFmpeg based audio splitter for Cue sheet files
Platform: all
Writer: jeanslack <jeanlucperni@gmail.com>
license: GPL3
Rev: Dec 22 2022
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
import shutil
import tempfile
import chardet
from deflacue.deflacue import CueParser
from ffcuesplitter.str_utils import (msgdebug,
                                     msg,
                                     )
from ffcuesplitter.utils import sanitize
from ffcuesplitter.exceptions import (InvalidFileError,
                                      FFCueSplitterError,
                                      )
from ffcuesplitter.ffprobe import ffprobe
from ffcuesplitter.ffmpeg import FFMpeg


class FFCueSplitter(FFMpeg):
    """
    This class implements an interface for retrieve the required
    data to accurately split audio CD images using FFmpeg.

    Usage:
            >>> from ffcuesplitter.cuesplitter import FFCueSplitter

        Splittings:
            >>> split = FFCueSplitter(filename)
            >>> split.open_cuefile()
            >>> split.do_operations()

        Get data tracks:
            >>> data = FFCueSplitter(filename, dry=True)
            >>> data.open_cuefile()
            >>> data.audiotracks  # trackdata
            >>> data.cue.meta.data  # cd_info
            >>> data.ffmpeg_arguments()

    For other options, read the examples on the wiki page:
    https://github.com/jeanslack/FFcuesplitter/wiki/Examples

    For a full meaning of the arguments to pass to the instance, read
    the __init__ docstring of this class.

    """
    def __init__(self,
                 filename,
                 outputdir: str = '.',
                 collection: str = '',
                 suffix: str = 'flac',
                 overwrite: str = "ask",
                 ffmpeg_cmd: str = 'ffmpeg',
                 ffmpeg_loglevel: str = "info",
                 ffprobe_cmd: str = 'ffprobe',
                 ffmpeg_add_params: str = '',
                 progress_meter: str = "standard",
                 dry: bool = False,
                 ):
        """
        ------------------
        Arguments meaning:
        ------------------

        filename:
                absolute or relative CUE sheet file ('filename.cue')
        outputdir:
                absolute or relative pathname to output files
        collection:
                auto-create additional sub-folders,
                one of ("artist+album", "artist", "album")
        suffix:
                output format, one of ("wav", "flac", "mp3", "ogg", "copy") .
        overwrite:
                overwriting options, one of "ask", "never", "always".
        ffmpeg_cmd:
                an absolute path command of ffmpeg
        ffmpeg_loglevel:
                one of "error", "warning", "info", "verbose", "debug" .
        ffprobe_cmd:
                an absolute path command of ffprobe.
        ffmpeg_add_params:
                additionals parameters of FFmpeg.
        progress_meter:
                one of 'tqdm', 'standard', default is 'standard'.
        dry:
                with `True`, perform the dry run with no changes
                done to filesystem.
        """
        super().__init__()

        self.kwargs = {'filename': os.path.abspath(filename)}
        self.kwargs['dirname'] = os.path.dirname(self.kwargs['filename'])
        if outputdir == '.':
            self.kwargs['outputdir'] = self.kwargs['dirname']
        else:
            self.kwargs['outputdir'] = os.path.abspath(outputdir)
        self.kwargs['collection'] = collection
        self.kwargs['format'] = suffix
        self.kwargs['overwrite'] = overwrite
        self.kwargs['ffmpeg_cmd'] = ffmpeg_cmd
        self.kwargs['ffmpeg_loglevel'] = ffmpeg_loglevel
        self.kwargs['ffprobe_cmd'] = ffprobe_cmd
        self.kwargs['ffmpeg_add_params'] = ffmpeg_add_params
        self.kwargs['progress_meter'] = progress_meter
        self.kwargs['dry'] = dry
        self.kwargs['logtofile'] = os.path.join(self.kwargs['dirname'],
                                                'ffcuesplitter.log')
        self.kwargs['tempdir'] = '.'
        self.audiotracks = None
        self.probedata = []
        self.cue_encoding = None  # data chardet
        self.cue = None
        self.testpatch = None  # set for test cases only
    # ----------------------------------------------------------------#

    def check_for_overwriting(self):
        """
        Checking options for overwriting files.
        """
        outputdir = self.kwargs['outputdir']
        overwr = self.kwargs['overwrite']
        tracks = self.audiotracks.copy()

        if overwr == 'always':
            msgdebug(info=("Overwrite existing file because "
                           "you specified the 'always' option"))
            return False

        if overwr == 'never':
            msgdebug(info=("Do not overwrite any files because "
                           "you specified 'never' option"))
            return True

        for data in tracks:  # self.audiotracks
            track = (f"{str(data['TRACK_NUM']).rjust(2, '0')} - "
                     f"{data['TITLE']}.{self.kwargs['format']}")
            pathfile = os.path.join(outputdir, track)

            if os.path.exists(pathfile):
                if overwr in ('n', 'N', 'y', 'Y', 'ask'):
                    while True:
                        msgdebug(warn=f"File already exists: "
                                 f"'{os.path.join(outputdir, track)}'")
                        overwr = input("Overwrite? [Y/n/always/never] > ")
                        if overwr in ('Y', 'y', 'n', 'N', 'always', 'never'):
                            break
                        msgdebug(err=f"Invalid option '{overwr}'")
                        continue
                if overwr == 'never':
                    msgdebug(info=("Do not overwrite any files because "
                                   "you specified 'never' option"))
                    return True

            if overwr in ('n', 'N'):
                del self.audiotracks[self.audiotracks.index(data)]

            elif overwr in ('y', 'Y', 'always', 'never', 'ask'):
                if overwr == 'always':
                    msgdebug(info=("Overwrite existing file because "
                                   "you specified the 'always' option"))
                    return False
        return False
    # ----------------------------------------------------------------#

    def move_files_to_outputdir(self):
        """
        All files are processed in a /temp folder. After the split
        operation is complete, all tracks are moved from /temp folder
        to output folder.

        Raises:
            FFCueSplitterError
        Returns:
            None

        """
        outputdir = self.kwargs['outputdir']

        for track in os.listdir(self.kwargs['tempdir']):
            try:
                shutil.move(os.path.join(self.kwargs['tempdir'], track),
                            os.path.join(outputdir, track))
            except Exception as error:
                raise FFCueSplitterError(error) from error
    # ----------------------------------------------------------------#

    def do_operations(self):
        """
        Automates the work in a temporary context using tempfile.

        Raises:
            FFCueSplitterError
        Returns:
            None
        """
        if self.check_for_overwriting() is True or self.audiotracks == []:
            return

        with tempfile.TemporaryDirectory(suffix=None,
                                         prefix='ffcuesplitter_',
                                         dir=None) as tmpdir:
            self.kwargs['tempdir'] = tmpdir
            self.ffmpeg_arguments()

            msgdebug(info=(f"Temporary Target: '{self.kwargs['tempdir']}'"))
            count = 0
            msgdebug(info="Extracting audio tracks (type Ctrl+c to stop):")

            for args, secs, title in zip(self.arguments,
                                         self.seconds,
                                         self.audiotracks):
                count += 1
                msg(f'\nTRACK {count}/{len(self.audiotracks)} '
                    f'>> "{title["TITLE"]}.{self.outsuffix}" ...')
                self.processing(args, secs)

            if self.kwargs['dry'] is True:
                return

            msg('\n')
            msgdebug(info="...done exctracting")
            msgdebug(info="Move files to: ",
                     tail=(f"\033[34m"
                           f"'{os.path.abspath(self.kwargs['outputdir'])}'"
                           f"\033[0m"))
            try:
                os.makedirs(self.kwargs['outputdir'],
                            mode=0o777, exist_ok=True)
            except Exception as error:
                raise FFCueSplitterError(error) from error

            self.move_files_to_outputdir()
    # ----------------------------------------------------------------#

    def get_track_duration(self, tracks):
        """
        Gets total duration of the source audio tracks for chunks
        calculation on the progress meter during ffmpeg executions.
        Given a total duration calculates the remains duration
        for the last track as well.

        This method is called by `cuefile_parser` method, Do not
        call this method directly.

        Raises:
            FFCueSplitterError
        Returns:
            tracks (list), all track data taken from the cue file.
        """
        if self.testpatch:
            probe = {'format': {'duration': 6.000000}}
        else:
            filename = tracks[0].get('FILE')
            cmd = self.kwargs['ffprobe_cmd']
            kwargs = {'loglevel': 'error', 'hide_banner': None}
            probe = ffprobe(filename, cmd=cmd, **kwargs)
            self.probedata.append(probe)

        time = []
        for idx in enumerate(tracks):
            if idx[0] != len(tracks) - 1:  # minus last
                trk = (tracks[idx[0] + 1]['START'] -
                       tracks[idx[0]]['START']) / (44100)
                time.append(trk)

        if not time:
            last = (float(probe['format']['duration']) -
                    tracks[0]['START'] / 44100)
        else:
            last = float(probe['format']['duration']) - sum(time)
        time.append(last)
        for keydur, remain in zip(tracks, time):
            keydur['DURATION'] = remain

        return tracks
    # ----------------------------------------------------------------#

    def deflacue_object_handler(self):
        """
        Handles `deflacue.CueParser` data.
        Raises:
            FFCueSplitterError: if no source audio file found
        Returns:
            'audiotracks' list object
        """
        self.audiotracks = []
        cd_info = self.cue.meta.data
        tracks = self.cue.tracks
        sourcenames = {k: [] for k in [str(x.file.path) for x in tracks]}

        if self.kwargs['collection']:  # Artist&Album names sanitize
            self.set_subdirs(cd_info.get('PERFORMER', 'No Artist name'),
                             cd_info.get('ALBUM', 'No Album name'))

        for track in enumerate(tracks):
            track_file = track[1].file.path

            if not track_file.exists():
                msgdebug(warn=(f'Source file `{track_file}` is not '
                               f'found. Track is skipped.'))

                if str(track_file) in sourcenames:
                    sourcenames.pop(str(track_file))
                    if not sourcenames:
                        raise FFCueSplitterError('No audio source files '
                                                 'found!')
                continue

            filename = (f"{sanitize(track[1].title)}")  # title names sanitize

            data = {'FILE': str(track_file), **cd_info, **track[1].data}
            data['TITLE'] = filename
            data['START'] = track[1].start

            if track[1].end != 0:
                data['END'] = track[1].end

            if f"{data['FILE']}" in sourcenames.keys():
                sourcenames[f'{data["FILE"]}'].append(data)

        for val in sourcenames.values():
            self.audiotracks += self.get_track_duration(val)

        return self.audiotracks
    # ----------------------------------------------------------------#

    def set_subdirs(self, performer, album):
        """
        Set sub-folders with artist and album names.
        This method reset the attribute `self.kwargs['outputdir']`
        adding the new folders sanitized to output destination.
        Raise FFCueSplitterError otherwise
        """
        subdirs = None

        if self.kwargs['collection'] == 'artist+album':
            subdirs = os.path.join(sanitize(performer), sanitize(album))

        elif self.kwargs['collection'] == 'artist':
            subdirs = f"{sanitize(performer)}"

        elif self.kwargs['collection'] == 'album':
            subdirs = f"{sanitize(album)}"

        if subdirs is not None:
            self.kwargs['outputdir'] = os.path.join(self.kwargs['outputdir'],
                                                    subdirs)
        else:
            raise FFCueSplitterError(f"Invalid collection arguments: "
                                     f"'{self.kwargs['collection']}'")
    # ----------------------------------------------------------------#

    def check_cuefile(self):
        """
        Cue file check
        """
        filesuffix = os.path.splitext(self.kwargs['filename'])[1]
        isfile = os.path.isfile(self.kwargs['filename'])

        if not isfile or filesuffix not in ('.cue', '.CUE'):
            raise InvalidFileError(f"Invalid CUE sheet file: "
                                   f"'{self.kwargs['filename']}'")
    # ----------------------------------------------------------------#

    def open_cuefile(self, testpatch=None):
        """
        Read cue file and start file parsing via deflacue package
        """
        if testpatch:
            self.testpatch = True

        self.check_cuefile()
        curdir = os.getcwd()
        os.chdir(self.kwargs['dirname'])

        with open(self.kwargs['filename'], 'rb') as file:
            cuebyte = file.read()
            self.cue_encoding = chardet.detect(cuebyte)

        parser = CueParser.from_file(self.kwargs['filename'],
                                     encoding=self.cue_encoding['encoding'])
        self.cue = parser.run()
        self.deflacue_object_handler()
        os.chdir(curdir)
