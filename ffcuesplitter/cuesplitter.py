"""
First release: January 16 2022

Name: cuesplitter.py
Porpose: FFmpeg based audio splitter for Cue sheet files
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

import os
import shutil
import tempfile
import chardet
from ffcuesplitter.str_utils import msgdebug, msg
from ffcuesplitter.exceptions import (InvalidFileError,
                                      ParserError,
                                      FFCueSplitterError,
                                      )
from ffcuesplitter.ffprobe import FFProbe
from ffcuesplitter.ffmpeg import FFMpeg
from ffcuesplitter.utils import pos_to_frames


class FFCueSplitter(FFMpeg):
    """
    This class implements an interface for parsing .cue sheet
    files in order to retrieve the required data to accurately
    split audio CD images using FFmpeg.

    Usage:
            >>> from ffcuesplitter.cuesplitter import FFCueSplitter
            >>> split = FFCueSplitter(filename='/home/user/my_file.cue')
            >>> split.open_cuefile()
            >>> split.do_operations()

    For a more advanced use of this class do not use `do_operations`
    method which automates all operations. The following examples are
    suggested:
            >>> from ffcuesplitter.cuesplitter import FFCueSplitter
            >>> split = FFCueSplitter(filename='/home/user/my_file.cue')
            >>> split.open_cuefile()
            >>> split.kwargs['tempdir'] = '/user/mytempdir'
            >>> split.arguments_building()
            >>> for args, secs in zip(split.arguments, split.seconds):
            ...     split.processing_with_tqdm_progress(args, secs)
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

        self.logfile = None
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
                                                'ffmpeg_output.log')

        filesuffix = os.path.splitext(self.kwargs['filename'])[1]
        isfile = os.path.isfile(self.kwargs['filename'])

        if not isfile or filesuffix not in ('.cue', '.CUE'):
            raise InvalidFileError(f"Invalid CUE sheet file: "
                                   f"'{self.kwargs['filename']}'")

        os.chdir(self.kwargs['dirname'])

        with open(self.kwargs['filename'], 'rb') as file:
            self.bdata = file.read()
            self.encoding = chardet.detect(self.bdata)
    # ----------------------------------------------------------#

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
    # ----------------------------------------------------------#

    def make_end_positions_and_durations(self, tracks):
        """
        Gets total duration of the big audio track via `ffprobe'
        command and defines the `END` frames for any tracks minus
        last. Given a total duration calculates the remains
        duration for the last track.

        This method is called by `cuefile_parser` method, Do not
        call this method directly.

        Raises:
            FFCueSplitterError
        Returns:
            tracks (list), all track data taken from the cue file.
        """
        probe = FFProbe(self.kwargs['ffprobe_url'],
                        self.kwargs['FILE'],
                        show_streams=False,
                        pretty=False
                        )
        frmt = probe.data_format()

        for lst in frmt:
            for dur in lst:
                if 'duration' in dur:
                    duration = dur.split('=')[1]
        time = []
        for idx, items in enumerate(tracks):
            if idx != len(tracks) - 1:  # minus last

                if 'pre_gap' in tracks[idx]:
                    trk = (tracks[idx + 1]['START'] -
                           tracks[idx]['START']) / (44100)  # get seconds
                    time.append(trk)
                    tracks[idx]['END'] = (tracks[idx + 1]['pre_gap'])
                else:
                    trk = (tracks[idx + 1]['START'] -
                           tracks[idx]['START']) / (44100)
                    time.append(trk)
                    tracks[idx]['END'] = (tracks[idx + 1]['START'])

        last = float(duration) - sum(time)
        time.append(last)
        for key, items in zip(tracks, time):
            key['DURATION'] = items

        return tracks
    # ----------------------------------------------------------#

    def do_operations(self):
        """
        This method automates the work in a temporary context.

        Raises:
            FFCueSplitterError
        Returns:
            None
        """
        with tempfile.TemporaryDirectory(suffix=None,
                                         prefix='ffcuesplitter_',
                                         dir=None) as tmpdir:
            self.kwargs['tempdir'] = tmpdir
            self.arguments_building()

            msgdebug(info=(f"Temporary Target: '{self.kwargs['tempdir']}'"))
            count = 0
            msgdebug(info="Extracting audio tracks (type Ctrl+c to stop):")

            for args, secs, title in zip(self.arguments,
                                         self.seconds,
                                         self.kwargs['tracks']):
                count += 1
                msg(f'\nTRACK {count}/{len(self.kwargs["tracks"])} '
                    f'>> "{title["TITLE"]}" ...')

                if self.kwargs['progress_meter'] == 'tqdm':
                    self.processing_with_tqdm_progress(args, secs)
                elif self.kwargs['progress_meter'] == 'mymet':
                    self.processing_with_mymet_progress(args, secs)
                elif self.kwargs['progress_meter'] == 'standard':
                    self.processing_with_standard_progress(args)

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
    # ----------------------------------------------------------#

    def cuefile_parser(self, lines):
        """
        CUE sheet file parsing. Gets cue file data for audio
        tags and defines the `START` frames for any tracks.
        This method is called by `open_cuefile` method,
        Do not call this method directly.

        Returns:
            tracks (list), all track data taken from the cue file.

        Raises:
            ParserError: if invalid data found
        """
        general = {}
        tracks = []
        for line in lines:
            if line.startswith('REM GENRE '):
                general['GENRE'] = line.split('"')[1]

            if line.startswith('REM DATE '):
                general['DATE'] = line.split()[2]

            if line.startswith('REM COMMENT '):
                general['COMMENT'] = line.split('"')[1]

            if line.startswith('PERFORMER '):
                general['ARTIST'] = line.split('"')[1]

            if line.startswith('TITLE '):
                general['ALBUM'] = line.split('"')[1]

            if line.startswith('FILE '):
                file = os.path.join(self.kwargs['dirname'], line.split('"')[1])
                self.kwargs['FILE'] = file  # get big audio file

            if line.startswith('  TRACK '):
                track = general.copy()
                track['TRACK'] = int(line.strip().split(' ')[1], 10)
                tracks.append(track)

            if line.startswith('    TITLE '):
                tracks[-1]['TITLE'] = line.split('"')[1]

            if line.startswith('    PERFORMER '):
                tracks[-1]['ARTIST'] = line.split('"')[1]

            if line.startswith('    INDEX 00 '):
                tracks[-1]['pre_gap'] = pos_to_frames(line)  # conv to frames

            if line.startswith('    INDEX 01 '):
                tracks[-1]['START'] = pos_to_frames(line)  # conv to frames

        if not tracks:
            raise ParserError(f'Parsing failed, no data found: {tracks}')

        return self.make_end_positions_and_durations(tracks)
    # ----------------------------------------------------------#

    def open_cuefile(self):
        """
        Defines a new UTF-8 encoded CUE sheet file as temporary
        file and retrieves tracks data to be splitted.

        Raises:
            ParserError: if invalid data found
        Returns:
            data 'tracks' object (dict)
        """
        with tempfile.NamedTemporaryFile(suffix='.cue',
                                         mode='w+',
                                         encoding='utf-8'
                                         ) as cuefile:
            cuefile.write(self.bdata.decode(self.encoding['encoding']))
            cuefile.seek(0)
            self.kwargs['tracks'] = self.cuefile_parser(cuefile.readlines())

        if not self.kwargs['tracks'] or not self.kwargs.get('FILE'):
            raise ParserError(f'Invalid data found: {self.kwargs}')

        return self.kwargs
