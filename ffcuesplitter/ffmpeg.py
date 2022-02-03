# -*- coding: UTF-8 -*-
"""
Name: ffmpeg.py
Porpose: builds arguments for FFmpeg processing.
Compatibility: Python3
Platform: all platforms
Author: Gianluca Pernigotto <jeanlucperni@gmail.com>
Copyright: (c) 202 Gianluca Pernigotto <jeanlucperni@gmail.com>
license: GPL3
Rev: February 03 2022
Code checker: flake8, pylint
########################################################

This file is part of Videomass.

   Videomass is free software: you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.

   Videomass is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with Videomass.  If not, see <http://www.gnu.org/licenses/>.
"""
import subprocess
import os
import sys
import platform
from tqdm import tqdm
from ffcuesplitter.exceptions import FFMpegError
from ffcuesplitter.str_utils import msg
from ffcuesplitter.utils import Popen

if not platform.system() == 'Windows':
    import shlex


class FFMpeg:
    """
    FFMpeg is a parent base class interface for FFCueSplitter.
    It represents FFmpeg command and arguments with their
    sub-processing.
    """
    DATACODECS = {'wav': 'pcm_s16le -ar 44100',
                  'flac': 'flac -ar 44100',
                  'ogg': 'libvorbis -ar 44100',
                  'mp3': 'libmp3lame -ar 44100',
                  }

    def __init__(self, **kwargs):
        """
        Constructor
        """
        self.kwargs = kwargs
        self.audiotracks = kwargs
        self.seconds = None
        self.arguments = None
        self.osplat = platform.system()
        self.outsuffix = None
    # -------------------------------------------------------------#

    def codec_setup(self, sourcef):
        """
        Returns codec arg based on given format
        """
        if self.kwargs['format'] == 'copy':
            self.outsuffix = os.path.splitext(sourcef)[1].replace('.', '')
            codec = '-c copy'

        else:
            self.outsuffix = self.kwargs['format']
            codec = f'-c:a {FFMpeg.DATACODECS[self.kwargs["format"]]}'

        return codec, self.outsuffix
    # -------------------------------------------------------------#

    def ffmpeg_arguments(self):
        """
        Builds `FFmpeg` arguments and calculates time seconds
        for each audio track.

        Returns:
            dict(arguments:[...], seconds:[...])
        """
        self.arguments = []
        self.seconds = []

        meters = {'tqdm': '-progress pipe:1 -nostats -nostdin', 'standard': ''}

        for track in self.audiotracks:
            codec, suffix = self.codec_setup(track["FILE"])
            metadata = {'ARTIST': track.get('PERFORMER', ''),
                        'ALBUM': track.get('ALBUM', ''),
                        'TITLE': track.get('TITLE', ''),
                        'TRACK': (str(track['TRACK_NUM']) + '/' +
                                  str(len(self.audiotracks))),
                        'DISCNUMBER': track.get('DISCNUMBER', ''),
                        'GENRE': track.get('GENRE', ''),
                        'DATE': track.get('DATE', ''),
                        'COMMENT': track.get('COMMENT', ''),
                        'DISCID': track.get('DISCID', ''),
                        }
            cmd = f'"{self.kwargs["ffmpeg_cmd"]}" '
            cmd += f' -loglevel {self.kwargs["ffmpeg_loglevel"]}'
            cmd += f" {meters[self.kwargs['progress_meter']]}"
            cmd += f' -i "{track["FILE"]}"'
            cmd += f" -ss {round(track['START'] / 44100, 6)}"  # ff to secs
            if 'END' in track:
                cmd += f" -to {round(track['END'] / 44100, 6)}"  # ff to secs
            for key, val in metadata.items():
                cmd += f' -metadata {key}="{val}"'
            cmd += f' {codec}'
            cmd += f" {self.kwargs['ffmpeg_add_params']}"
            cmd += ' -y'
            num = str(track['TRACK_NUM']).rjust(2, '0')
            name = f'{num} - {track["TITLE"]}.{suffix}'
            cmd += f' "{os.path.join(self.kwargs["tempdir"], name)}"'
            self.arguments.append(cmd)
            self.seconds.append(track['DURATION'])

        return {'arguments': self.arguments, 'seconds': self.seconds}
    # --------------------------------------------------------------#

    def processing(self, arg, secs):
        """
        Redirect to required processing
        """
        if self.kwargs['progress_meter'] == 'tqdm':
            cmd = arg if self.osplat == 'Windows' else shlex.split(arg)
            if self.kwargs['dry'] is True:
                msg(cmd)  # stdout cmd in dry mode
                return
            self.processing_with_tqdm_progress(cmd, secs)

        elif self.kwargs['progress_meter'] == 'standard':
            cmd = arg if self.osplat == 'Windows' else shlex.split(arg)
            if self.kwargs['dry'] is True:
                msg(cmd)  # stdout cmd in dry mode
                return
            self.processing_with_standard_progress(cmd)
    # --------------------------------------------------------------#

    def processing_with_tqdm_progress(self, cmd, seconds):
        """
        FFmpeg sub-processing showing a tqdm progress meter
        for each loop. Also writes a log file to the same
        destination folder as the .cue file .

        Usage for get seconds elapsed:
         progbar = tqdm(total=round(seconds), unit="s", dynamic_ncols=True)
         progbar.clear()
         previous_s = 0

            s_processed = round(int(output.split('=')[1]) / 1_000_000)
            s_increase = s_processed - previous_s
            progbar.update(s_increase)
            previous_s = s_processed

        Raises:
            FFMpegError
        Returns:
            None
        """
        progbar = tqdm(total=100,
                       unit="s",
                       dynamic_ncols=True
                       )
        progbar.clear()

        try:
            with open(self.kwargs['logtofile'], "w", encoding='utf-8') as log:
                log.write(f'\nCOMMAND: {cmd}')
                with Popen(cmd,
                           stdout=subprocess.PIPE,
                           stderr=log,
                           bufsize=1,
                           universal_newlines=True) as proc:

                    for output in proc.stdout:
                        if "out_time_ms" in output.strip():
                            s_processed = int(output.split('=')[1]) / 1_000_000
                            percent = s_processed / seconds * 100
                            progbar.update(round(percent) - progbar.n)

                    if proc.wait():  # error
                        progbar.close()
                        raise FFMpegError(f"ffmpeg FAILED: See log details: "
                                          f"'{self.kwargs['logtofile']}'"
                                          f"\nExit status: {proc.wait()}")

        except (OSError, FileNotFoundError) as excepterr:
            progbar.close()
            raise FFMpegError(excepterr) from excepterr

        except KeyboardInterrupt:
            # proc.kill()
            progbar.close()
            proc.terminate()
            sys.exit("\n[KeyboardInterrupt] FFmpeg process terminated.")

        progbar.close()
    # --------------------------------------------------------------#

    def processing_with_standard_progress(self, cmd):
        """
        FFmpeg sub-processing with stderr output to console.
        The output depending on the ffmpeg loglevel option.
        Raises:
            FFMpegError
        Returns:
            None
        """
        with open(self.kwargs['logtofile'], "w", encoding='utf-8') as log:
            log.write(f'COMMAND: {cmd}')
        try:
            subprocess.run(cmd, check=True, shell=False)

        except FileNotFoundError as err:
            raise FFMpegError(f"{err}") from err

        except subprocess.CalledProcessError as err:
            raise FFMpegError(f"ffmpeg FAILED: {err}") from err

        except KeyboardInterrupt:
            sys.exit("\n[KeyboardInterrupt]")
