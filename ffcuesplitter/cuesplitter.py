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
import sys
import shutil
import subprocess
import shlex
import platform
import tempfile
import datetime
import chardet
from ffcuesplitter.str_utils import msgdebug, msg
from ffcuesplitter.exceptions import (InvalidFileError,
                                      ParserError,
                                      FFCueSplitterError
                                      )
from ffcuesplitter.ffprobe_parser import FFProbe

# ------------------------------------------------------------------------

def pairwise(iterable):
    """
    Return a zip object from iterable.
    This function is used by the update_display method.
    ----
    USE:

    after splitting ffmpeg's progress strings such as:
    output = "frame= 1178 fps=155 q=29.0 size=    2072kB time=00:00:39.02
              bitrate= 435.0kbits/s speed=5.15x  "
    in a list as:
    iterable = ['frame', '1178', 'fps', '155', 'q', '29.0', 'size', '2072kB',
                'time', '00:00:39.02', 'bitrate', '435.0kbits/s', speed',
                '5.15x']
    for x, y in pairwise(iterable):
        print(x,y)

    <https://stackoverflow.com/questions/5389507/iterating-over-every-
    two-elements-in-a-list>

    """
    itobj = iter(iterable)  # list_iterator object
    return zip(itobj, itobj)  # zip object pairs from list iterable object
# ----------------------------------------------------------------------#


def pos_to_frames(pos) -> int:
    """Converts position (mm:ss:ff) into frames.

    :param pos:

    """
    minutes, seconds, frames = map(int, pos.strip().split(' ')[2].split(':'))

    #minutes, seconds, frames = map(int, pos.split(':'))
    seconds = (minutes * 60) + seconds
    rate = 44100
    return (seconds * rate) + (frames * (rate // 75))
# ----------------------------------------------------------------------#


def frames_to_seconds(frames):
    """Converts frames (10407600) to seconds (236.0) and then
    converts them to a time format string (0:03:56) using datetime.
    """
    rate = frames / 44100
    return str(datetime.timedelta(seconds=rate))
# ----------------------------------------------------------------------#


def get_output_seconds_from_ffmpeg(timehuman):
    """
    This is the old implementation to get time human to seconds,
    e.g. get_output_seconds_from_ffmpeg('00:02:00').
    Return int(seconds) object.

    """
    if timehuman == 'N/A':
        return int('0')

    pos = timehuman.split(':')
    hours, minutes, seconds = int(pos[0]), int(pos[1]), float(pos[2])

    return hours * 3600 + minutes * 60 + seconds

# ------------------------------------------------------------------------


class Popen(subprocess.Popen):
    """Inherit subprocess.Popen class
    """
    if platform.system() == 'Windows':
        _startupinfo = subprocess.STARTUPINFO()
        _startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    else:
        _startupinfo = None

    def __init__(self, *args, **kwargs):
        """Constructor
        """
        super().__init__(*args, **kwargs, startupinfo=self._startupinfo)

    #def communicate_or_kill(self, *args, **kwargs):
        #return process_communicate_or_kill(self, *args, **kwargs)


def run(command, duration, dry):
    """
    File Processing using FFmpeg
    """
    if dry is True:
        msg(command)
        return

    if not platform.system() == 'Windows':
        command = shlex.split(command)
    else:
        command = command

    try:
        with Popen(command,
                   stderr=subprocess.PIPE,
                   bufsize=1,
                   universal_newlines=True) as proc:

            for output in proc.stderr:
                #print(output)
                # WARNING USE A LOGGER HERE
                if 'time=' in output.strip():  # ...in processing
                    i = output.index('time=') + 5
                    pos = output[i:].split()[0]
                    sec = get_output_seconds_from_ffmpeg(pos)
                    percentage = round((sec / duration) * 100 if
                                        duration != 0 else 100)

                    # WARNING evaluate what to do
                    out = [a for a in "=".join(output.split()).split('=') if a]
                    ffprog = []
                    for key, val in pairwise(out):
                        ffprog.append(f"{key}: {val} | ")
                    sys.stdout.write(f"    progress: {str(int(percentage))}%"
                                     f" | {''.join(ffprog)}\r")
                    sys.stdout.flush()

            if proc.wait():  # error
                return (f"log file: "
                        f"'{os.path.join(os.getcwd(),'ffmpeg_output.log')}'"
                        f"\nFFmpeg exit with status: {proc.wait()}")

    except (OSError, FileNotFoundError) as excepterr:
        return excepterr

    except KeyboardInterrupt:
        # proc.kill()
        proc.terminate()
        sys.exit("\n[KeyboardInterrupt] FFmpeg process terminated.")

    return None
# ------------------------------------------------------------------------


class FFCueSplitter():
    """
    This class implements an interface to securely wrap shnsplit
    and cuetag tools: Since neither shnsplit nor cuetag correctly
    support reading CUE sheet files with encodings other than
    ASCII/UTF-8, the FFCueSplitter class allows you to get around this
    problem by working in a temporary context without modifying the
    source files.

    Other useful functions of the FFCueSplitter class can
    be configured: you can choose between 6 audio output formats;
    you can set an output folder; you can control overwriting of
    files. For more details see the doc string of the constructor
    of this class.

    Usage:
            >>> from ffcuesplitter.cuesplitter import FFCueSplitter
            >>> kwargs = {'filename': '/home/user/my_file.cue',
                          'outputdir': '/home/user/some_other_dir',
                          'format': 'flac',
                          'overwrite': 'ask'
                          }
            >>> split = FFCueSplitter(**kwargs)
            >>> split.open_cuefile()
            >>> split.do_operations()
    """
    def __init__(self,
                 filename=str(''),
                 outputdir=str('.'),
                 suffix=str('flac'),
                 overwrite=str('ask'),
                 ffmpeg_url=str('ffmpeg'),
                 ffmpeg_loglevel=str('warning'),
                 ffprobe_url=str('ffprobe'),
                 ffmpeg_add_params=str(''),
                 dry=bool(False)
                 ):
        """
            'filename': absolute or relative CUE sheet file
            'outputdir': absolute or relative pathname to output files
            'format': output format, one of "wav", "wv", "flac", "alac",
                      "mp3", "ogg" .
            'overwrite': controls for overwriting files,
                         one of "ask", "never", "always"
                         Also see `move_files_on_outputdir`
                         method.
        """
        self.kwargs = {'filename': os.path.abspath(filename)}
        self.kwargs['dirname'] = os.path.dirname(self.kwargs['filename'])
        if outputdir == '.':
            self.kwargs['outputdir'] = self.kwargs['dirname']
        else:
            self.kwargs['outputdir'] = os.path.abspath(outputdir)
        self.kwargs['format'] = suffix
        self.kwargs['overwrite'] = overwrite
        self.kwargs['ffmpeg'] = ffmpeg_url
        self.kwargs['ffloglevel'] = ffmpeg_loglevel
        self.kwargs['ffprobe'] = ffprobe_url
        self.kwargs['ffmpeg_add_params'] = ffmpeg_add_params
        self.kwargs['dry'] = dry

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
        This method is called by `do_operations` method. Do not call
        this method directly.
        Raises:
            FFCueSplitterError
        Returns:
            None otherwise.

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

    def command_building(self):
        """Builds `FFmpeg` commands.
        This method is called by `do_operations` method. Do not call
        this method directly.
        Raises:
            FFCueSplitterError
        Returns:
            (commands list + duration list)
        """
        command = []
        time = []
        datacodecs = {'wav': ['pcm_s16le', 'wav'],
                      'wv': ['libwavpack', 'wv'],
                      'flac': ['flac', 'flac'],
                      'm4a': ['alac', 'm4a'],
                      'ogg': ['libvorbis', 'ogg'],
                      'mp3': ['libmp3lame', 'mp3'],
                      }
        codec = datacodecs[self.kwargs['format']][0]
        outext = datacodecs[self.kwargs['format']][1]


        for track in self.kwargs['titles']:
            metadata = {'ARTIST': track.get('ARTIST', ''),
                        'ALBUM': track.get('ALBUM', ''),
                        'TITLE': track.get('TITLE', ''),
                        'TRACK': (str(track['TRACK']) + '/' +
                                  str(len(self.kwargs['titles']))),
                        'GENRE': track.get('GENRE', ''),
                        'DATE': track.get('DATE', ''),
                        'COMMENT': track.get('COMMENT', ''),
                        }
            cmd = f'"{self.kwargs["ffmpeg"]}"'
            cmd += (f" -loglevel {self.kwargs['ffloglevel']} "
                    "-stats -hide_banner")
            cmd += f' -i "{self.kwargs["FILE"]}"'
            cmd += f" -ss {frames_to_seconds(track['START'])}"

            if 'END' in track:
                cmd += f" -to {frames_to_seconds(track['END'])}"

            for key, val in metadata.items():
                cmd += f' -metadata {key}="{val}"'

            cmd += f' -c:a {codec}'
            cmd += f" {self.kwargs['ffmpeg_add_params']}"
            name = (f"{track['TRACK']} - {track.get('TITLE', '')}.{outext}")
            cmd += f' "{os.path.join(self.kwargs["tempdir"], name)}"'
            command.append(cmd)
            time.append(track['TIME'])

        return command, time
    # ----------------------------------------------------------#

    def make_end_positions_and_durations(self, tracks):
        """
        convert to time
        """
        probe = FFProbe(self.kwargs['ffprobe'],
                        self.kwargs['FILE'],
                        pretty=False
                        )
        if probe.error_check():
            raise FFCueSplitterError(probe.error)
        frmt = probe.data_format()
        for lst in frmt:
            for dur in lst:
                if 'duration' in dur:
                    duration = dur.split('=')[1]
        time = []
        for idx, items in enumerate(tracks):
            if idx != len(tracks) - 1:

                if 'pre_gap' in tracks[idx]:
                    trk = (tracks[idx + 1]['START'] -
                           tracks[idx]['START']) / (44100)
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
            key['TIME'] = items

        return tracks
    # ----------------------------------------------------------#

    def do_operations(self):
        """
        Defines a temporary folder for working safely with files.
        This method calls following methods of this class:
            - self.command_building()
            - self.move_files_on_outputdir
        """
        with tempfile.TemporaryDirectory(suffix=None,
                                         prefix='ffcuesplitter_',
                                         dir=None) as tmpdir:
            self.kwargs['tempdir'] = tmpdir
            items = self.command_building()
            #self.commands, self.durations = self.command_building()
            count = 0
            msg('\n')
            msgdebug(info="Extracting audio tracks (type Ctrl+c to stop):")
            for line, duration, title in zip(items[0],
                                              items[1],
                                              self.kwargs['titles']):
                count += 1
                msg(f'\nTRACK {count}/{len(items[1])} '
                    f'>> "{title["TITLE"]}" ...')
                proc = run(line, duration, self.kwargs['dry'])
                if proc:
                    raise FFCueSplitterError(proc)
            msg('\n')
            try:
                os.makedirs(self.kwargs['outputdir'],
                            mode=0o777, exist_ok=True)
            except Exception as error:
                raise FFCueSplitterError(error) from error

            self.move_files_on_outputdir()
            msgdebug(info="Target (output) path: ",
                     tail=(f"\033[34m"
                           f"'{os.path.abspath(self.kwargs['outputdir'])}'"
                           f"\033[0m"))
    # ----------------------------------------------------------#

    def cuefile_parser(self, lines):
        """
        Gets the large audio filename and enumerates the titles of
        all the tracks to be split.

        Returns:
            A dictionary with FILE and TRACK keys, where FILE is the
            name of audio file associated with cue sheet file, TRACK
            is a progressive digit of any audio track.
            A empty dictionary otherwise.

        Raises:
            ParserError: if found invalid data
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
                self.kwargs['FILE'] = file

            if line.startswith('  TRACK '):
                track = general.copy()
                track['TRACK'] = int(line.strip().split(' ')[1], 10)
                tracks.append(track)

            if line.startswith('    TITLE '):
                tracks[-1]['TITLE'] = line.split('"')[1]

            if line.startswith('    PERFORMER '):
                tracks[-1]['ARTIST'] = line.split('"')[1]

            if line.startswith('    INDEX 00 '):
                tracks[-1]['pre_gap'] = pos_to_frames(line)

            if line.startswith('    INDEX 01 '):
                tracks[-1]['START'] = pos_to_frames(line)

        if not tracks:
            raise ParserError(f'Parsing failed, no data found: {tracks}')

        #print(tracks)

        return self.make_end_positions_and_durations(tracks)
    # ----------------------------------------------------------#

    def open_cuefile(self):
        """
        Defines a new UTF-8 encoded CUE sheet file as temporary
        file and retrieves titles names to be splitted.

        Returns:
            data dict
        """
        with tempfile.NamedTemporaryFile(suffix='.cue',
                                         mode='w+',
                                         encoding='utf-8'
                                         ) as cuefile:
            cuefile.write(self.bdata.decode(self.encoding['encoding']))
            cuefile.seek(0)
            self.kwargs['titles'] = self.cuefile_parser(cuefile.readlines())

        if not self.kwargs['titles'] or not self.kwargs.get('FILE'):
            raise ParserError(f'Invalid data found: {self.kwargs}')

        return self.kwargs
