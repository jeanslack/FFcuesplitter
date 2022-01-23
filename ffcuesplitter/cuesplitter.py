"""
First release: January 16 2022

Name: cuesplitter.py
Porpose: FFmpeg based audio splitter for Cue sheet files
Platform: MacOs, Gnu/Linux, FreeBSD
Writer: jeanslack <jeanlucperni@gmail.com>
license: GPL3
Rev: January 22 2022
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

import os
import shutil
import tempfile
import chardet
from deflacue.deflacue import CueParser
from ffcuesplitter.str_utils import msgdebug, msg
from ffcuesplitter.exceptions import (InvalidFileError,
                                      FFCueSplitterError,
                                      )
from ffcuesplitter.ffprobe import FFProbe
from ffcuesplitter.ffmpeg import FFMpeg


class FFCueSplitter(FFMpeg):
    """
    This class implements an interface for retrieve the required
    data to accurately split audio CD images using FFmpeg.

    Usage:
            >>> from ffcuesplitter.cuesplitter import FFCueSplitter
            >>> split = FFCueSplitter(filename='/home/user/my_file.cue')
            >>> split.open_cuefile()
            >>> split.do_operations()

    For a more advanced use of this class follow this examples:
            >>> from ffcuesplitter.cuesplitter import FFCueSplitter
            >>> split = FFCueSplitter(filename='/home/user/my_file.cue')
            >>> split.open_cuefile()
            >>> split.kwargs['tempdir'] = '/tmp/mytempdir'
            >>> split.ffmpeg_arguments()
            >>> for args, secs in zip(split.arguments, split.seconds):
            ...     split.processing(args, secs)
            >>> split.move_files_on_outputdir()

    For a full meaning of the arguments to pass to the instance, read
    the __init__ docstring of this class.

    """
    def __init__(self,
                 filename=str(''),
                 outputdir=str('.'),
                 suffix=str('flac'),
                 overwrite=str('ask'),
                 ffmpeg_url=str('ffmpeg'),
                 ffmpeg_loglevel=str('info'),
                 ffprobe_url=str('ffprobe'),
                 ffmpeg_add_params=str(''),
                 progress_meter=str('standard'),
                 dry=bool(False)
                 ):
        """
        ------------------
        Arguments meaning:
        ------------------

        filename:
                absolute or relative CUE sheet file
        outputdir:
                absolute or relative pathname to output files
        suffix:
                output format, one of ("wav", "wv", "flac",
                                       "mp3", "ogg", "m4a") .
        overwrite:
                controls for overwriting files, one of "ask",
                "never", "always". Also see `move_files_on_outputdir`
                method.
        ffmpeg_url:
                a custon path of ffmpeg
        ffmpeg_loglevel:
                one of "error", "warning", "info", "verbose", "debug" .
        ffprobe_url:
                a custon path of ffprobe.
        ffmpeg_add_params:
                additionals parameters of FFmpeg
        progress_meter:
                one of 'tqdm', 'mymet', 'standard', default is
                'standard'. Note, this option has no effect if
                you don't use the `do_operations` method.
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
        self.kwargs['format'] = suffix
        self.kwargs['overwrite'] = overwrite
        self.kwargs['ffmpeg_url'] = ffmpeg_url
        self.kwargs['ffmpeg_loglevel'] = ffmpeg_loglevel
        self.kwargs['ffprobe_url'] = ffprobe_url
        self.kwargs['ffmpeg_add_params'] = ffmpeg_add_params
        self.kwargs['progress_meter'] = progress_meter
        self.kwargs['dry'] = dry
        self.kwargs['logtofile'] = os.path.join(self.kwargs['dirname'],
                                                'ffcuesplitter.log')
        self.audiotracks = None
        self.cue = None
    # ----------------------------------------------------------------#

    def move_files_on_outputdir(self):
        """
        All files are processed in a /temp folder. After the split
        operation is complete, all tracks are moved from /temp folder
        to output folder. Here evaluates what to do if files already
        exists on output folder.

        Raises:
            FFCueSplitterError
        Returns:
            None

        """
        outputdir = self.kwargs['outputdir']
        overwr = self.kwargs['overwrite']

        for track in os.listdir(self.kwargs['tempdir']):
            if os.path.exists(os.path.join(outputdir, track)):
                if overwr in ('n', 'N', 'y', 'Y', 'ask'):
                    while True:
                        msgdebug(warn=f"File already exists: "
                                 f"'{os.path.join(outputdir, track)}'")
                        overwr = input("Overwrite [Y/n/always/never]? > ")
                        if overwr in ('Y', 'y', 'n', 'N', 'always', 'never'):
                            break
                        msgdebug(err=f"Invalid option '{overwr}'")
                        continue
                if overwr == 'never':
                    msgdebug(info=("Do not overwrite any files because "
                                   "you specified 'never' option"))
                    return None

            if overwr in ('y', 'Y', 'always', 'never', 'ask'):
                if overwr == 'always':
                    msgdebug(info=("Overwrite existing file because "
                                   "you specified the 'always' option"))
                try:
                    shutil.move(os.path.join(self.kwargs['tempdir'], track),
                                os.path.join(outputdir, track))

                except Exception as error:
                    raise FFCueSplitterError(error) from error

        return None
    # ----------------------------------------------------------------#

    def do_operations(self):
        """
        Automates the work in a temporary context.

        Raises:
            FFCueSplitterError
        Returns:
            None
        """
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
                    f'>> "{title["TITLE"]}" ...')
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

            self.move_files_on_outputdir()
    # ----------------------------------------------------------------#

    def get_duration_tracks(self, tracks):
        """
        Gets total duration of the source audio tracks via `ffprobe'
        command and sets `duration key` for progress meter.
        Given a total duration calculates the remains
        duration for the last track.

        This method is called by `cuefile_parser` method, Do not
        call this method directly.

        Raises:
            FFCueSplitterError
        Returns:
            tracks (list), all track data taken from the cue file.
        """
        probe = FFProbe(self.kwargs['ffprobe_url'],
                        tracks[0].get('FILE'),
                        show_streams=False,
                        pretty=False
                        )
        duration = probe.data_format('duration')

        time = []
        for idx, items in enumerate(tracks):
            if idx != len(tracks) - 1:  # minus last
                trk = (tracks[idx + 1]['START'] -
                       tracks[idx]['START']) / (44100)
                time.append(trk)

        if not time:
            last = float(duration) - tracks[0]['START'] / 44100
        else:
            last = float(duration) - sum(time)
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

        def sanitize(val: str) -> str:
            return val.replace('/', '')

        tracks = self.cue.tracks
        sourcenames = {k: [] for k in [str(x.file.path) for x in tracks]}

        for idx, track in enumerate(tracks):
            track_file = track.file.path

            if not track_file.exists():
                msgdebug(warn=(f'Source file `{track_file}` is not '
                               f'found. Track is skipped.'))

                if str(track_file) in sourcenames:
                    sourcenames.pop(str(track_file))
                    if not sourcenames:
                        raise FFCueSplitterError('No audio source files '
                                                 'found!')
                continue

            filename = (f"{sanitize(track.title)}.{self.kwargs['format']}")

            data = {'FILE': str(track_file), **track.data, **cd_info}
            data['TITLE'] = filename
            data['START'] = track.start

            if track.end != 0:
                data['END'] = track.end

            if f"{data['FILE']}" in sourcenames.keys():
                sourcenames[f'{data["FILE"]}'].append(data)

        for val in sourcenames.values():
            self.audiotracks += self.get_duration_tracks(val)

        return self.audiotracks
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

    def open_cuefile(self):
        """
        Read cue file and start file parsing via deflacue package
        """
        self.check_cuefile()
        os.chdir(self.kwargs['dirname'])

        with open(self.kwargs['filename'], 'rb') as file:
            cuebyte = file.read()
            encoding = chardet.detect(cuebyte)

        parser = CueParser.from_file(self.kwargs['filename'],
                                     encoding=encoding['encoding'])
        self.cue = parser.run()
        self.deflacue_object_handler()
