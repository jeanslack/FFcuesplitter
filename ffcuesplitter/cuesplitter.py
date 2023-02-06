"""
First release: January 16 2022

Name: cuesplitter.py
Porpose: FFmpeg based audio splitter for Cue sheet files
Platform: all
Writer: jeanslack <jeanlucperni@gmail.com>
license: GPL3
Copyright: (C) 2023 Gianluca Pernigotto <jeanlucperni@gmail.com>
Rev: Feb 06 2023
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
import logging
from dataclasses import dataclass, asdict
import chardet
from deflacue.deflacue import CueParser
from ffcuesplitter.utils import sanitize
from ffcuesplitter.exceptions import (InvalidFileError,
                                      FFCueSplitterError,
                                      )
from ffcuesplitter.ffprobe import ffprobe
from ffcuesplitter.ffmpeg import FFMpeg


@dataclass
class DataArgs:
    """
    Object to pass and get `ffcuesplitter` arguments
    """
    filename: str
    outputdir: str = '.'
    collection: str = ''
    outputformat: str = 'flac'
    overwrite: str = "ask"
    ffmpeg_cmd: str = 'ffmpeg'
    ffmpeg_loglevel: str = "info"
    ffprobe_cmd: str = 'ffprobe'
    ffmpeg_add_params: str = ''
    progress_meter: str = "standard"
    dry: bool = False
    prg_loglevel: str = 'info'
    testpatch: bool = False  # must be `True` only using test cases

    def asdict(self) -> dict:
        """return dict object"""
        return asdict(self)


class FFCueSplitter(FFMpeg):
    """
    This is a subclass derived from the `FFMpeg` base
    class, it implements an interface to fetch the
    required data to accurately split audio tracks
    from a CD image using FFmpeg.

    Usage:
        >>> from ffcuesplitter.cuesplitter import FFCueSplitter
        >>> getdata = FFCueSplitter(**kwargs)
        >>> tracks = getdata.audiotracks
        >>> getdata.commandargs(tracks)

        Get additional data:

        >>> getdata.cue.meta.data  # CD info
        >>> getdata.probedata  # the ffprobe data of sources audio files

    For more options, visit the wiki page at:
    https://github.com/jeanslack/FFcuesplitter/wiki/Usage-from-Python

    For a full meaning of the key arguments to pass to the instance, read
    the __init__ docstring of this class or type `help(FFCueSplitter)`.

    """
    def __init__(self, **kwargs):
        """
        ------------------
        Arguments meaning:
        ------------------

        filename:
                absolute or relative CUE sheet file ('filename.cue').
        outputdir:
                absolute or relative pathname to output files.
        collection:
                auto-create additional sub-dirs,
                one of ("artist+album", "artist", "album").
        outputformat:
                output format, one of
                ("wav", "flac", "mp3", "ogg", "opus", "copy").
        overwrite:
                overwriting options, one of ("ask", "never", "always").
        ffmpeg_cmd:
                an absolute path command of ffmpeg.
        ffmpeg_loglevel:
                one of ("error", "warning", "info", "verbose", "debug").
        ffprobe_cmd:
                an absolute path command of ffprobe.
        ffmpeg_add_params:
                additionals parameters of FFmpeg.
        progress_meter:
                one of ('tqdm', 'standard'), default is 'standard'.
        dry:
                with `True`, perform the dry run with no changes
                done to filesystem.
        prg_loglevel:
                Set the logging level of tracking events to console,
                one of ("error", "warning", "info", "debug"),
                default is `info`.
        testpatch:
                Used for test cases only (do not use for normal tasks).
        """
        super().__init__()

        argsdata = DataArgs(**kwargs)
        self.kwargs = argsdata.asdict()

        loglevel = self.kwargs['prg_loglevel']
        nlev = getattr(logging, loglevel.upper(), None)
        if not isinstance(nlev, int):
            raise ValueError(f'Invalid log level: {loglevel}')
        logging.basicConfig(format='%(levelname)s: %(message)s', level=nlev)

        self.kwargs['filename'] = os.path.abspath(self.kwargs['filename'])
        self.kwargs['dirname'] = os.path.dirname(self.kwargs['filename'])
        outputdir = self.kwargs['outputdir']
        if outputdir == '.':
            self.kwargs['outputdir'] = self.kwargs['dirname']
        else:
            self.kwargs['outputdir'] = os.path.abspath(outputdir)
        self.kwargs['logtofile'] = os.path.join(self.kwargs['outputdir'],
                                                'ffcuesplitter.log')
        self.kwargs['tempdir'] = '.'

        self.audiotracks = None
        self.probedata = []
        self.cue_encoding = None  # data chardet
        self.cue = None  # data deflacue

        self.open_cuefile()  # requires to open cue file first
    # ----------------------------------------------------------------#

    def clear_logfile(self):
        """
        Clear the log file before writing it back
        """
        if os.path.exists(self.kwargs['logtofile']):
            if os.path.isfile(self.kwargs['logtofile']):
                with open(self.kwargs['logtofile'],
                          "w",
                          encoding='utf-8',
                          ):
                    logging.debug("Log file clearing: '%s'",
                                  self.kwargs['logtofile'])
    # ----------------------------------------------------------------#

    def get_track_durations(self, audiotracks):
        """
        Gets audio track durations for chunks calcs.
        This method is called by `deflacue_object_handler` method.

        Returns:
            An `audiotracks` object updated with a DURATION
            key and a definition of time in seconds as a value
            (of type float) for each track.

        """
        if self.kwargs['testpatch']:
            probe = {'format': {'duration': 6.000000}}
        else:
            filename = audiotracks[0].get('FILE')
            cmd = self.kwargs['ffprobe_cmd']
            kwargs = {'loglevel': 'error', 'hide_banner': None}
            probe = ffprobe(filename, cmd=cmd, **kwargs)
            self.probedata.append(probe)

        durations = []
        for idx in enumerate(audiotracks):
            if idx[0] != len(audiotracks) - 1:  # minus last
                trk = (audiotracks[idx[0] + 1]['START']
                       - audiotracks[idx[0]]['START']) / (44100)
                durations.append(trk)

        if not durations:
            last = (float(probe['format']['duration'])
                    - audiotracks[0]['START'] / 44100)
        else:
            last = float(probe['format']['duration']) - sum(durations)
        durations.append(last)

        for keydur, remain in zip(audiotracks, durations):
            keydur['DURATION'] = remain

        return audiotracks
    # ----------------------------------------------------------------#

    def deflacue_object_handler(self):
        """
        Handles `CueParser` data from deflacue.
        Raises:
            FFCueSplitterError: if no source audio file found
        Returns:
            'audiotracks' list object
        """
        self.audiotracks = []
        cd_info = self.cue.meta.data
        tracks = self.cue.tracks
        sourcenames = {k: [] for k in [str(x.file.path) for x in tracks]}

        if self.kwargs['collection']:  # Artist&Album names to sanitize
            self.set_subdirs(cd_info.get('PERFORMER', 'Unknown Artist'),
                             cd_info.get('ALBUM', 'Unknown Album'))
        self.clear_logfile()  # erases previous log file data

        for track in enumerate(tracks):
            track_file = track[1].file.path

            if not track_file.exists():
                logging.warning('Not found: `%s`. '
                                'Track is skipped.', track_file)

                if str(track_file) in sourcenames:
                    sourcenames.pop(str(track_file))
                    if not sourcenames:
                        raise FFCueSplitterError('No audio files found!')
                continue

            filename = (f"{sanitize(track[1].title)}")  # titles to sanitize

            data = {'FILE': str(track_file), **cd_info, **track[1].data}
            data['TITLE'] = filename
            data['START'] = track[1].start

            if track[1].end != 0:
                data['END'] = track[1].end

            if f"{data['FILE']}" in sourcenames.keys():
                sourcenames[f'{data["FILE"]}'].append(data)

        for val in sourcenames.values():
            self.audiotracks += self.get_track_durations(val)

        return self.audiotracks
    # ----------------------------------------------------------------#

    def set_subdirs(self, performer, album):
        """
        Set artist/album-name as possible sub-directories
        for audio collections. This method overwrites
        `self.kwargs['outputdir']` and `self.kwargs['logtofile']`
        attributes joining the sanitized audio collection names
        to the files destination directory.

        Raise FFCueSplitterError otherwise
        """
        subdirs = None

        if self.kwargs['collection'] == 'artist+album':
            subdirs = os.path.join(sanitize(performer), sanitize(album))

        elif self.kwargs['collection'] == 'artist':
            subdirs = f"{sanitize(performer)}"

        elif self.kwargs['collection'] == 'album':
            subdirs = f"{sanitize(album)}"

        if subdirs:
            self.kwargs['outputdir'] = os.path.join(self.kwargs['outputdir'],
                                                    subdirs)
            self.kwargs['logtofile'] = os.path.join(self.kwargs['outputdir'],
                                                    'ffcuesplitter.log')
        else:
            raise FFCueSplitterError(f"Invalid argument: "
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

    def open_cuefile(self):
        """
        Gets cue file bytes for character set encoding
        then starts file parsing via deflacue.
        """
        logging.debug("Processing: '%s'", self.kwargs['filename'])
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
