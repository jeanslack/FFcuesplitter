# -*- coding: UTF-8 -*-
"""
Name: ffmpeg.py
Porpose: builds arguments and commands for processing with FFmpeg
Compatibility: Python3
Platform: all platforms
Author: Gianluca Pernigotto <jeanlucperni@gmail.com>
Copyright: (c) 202 Gianluca Pernigotto <jeanlucperni@gmail.com>
license: GPL3
Rev: Jannuary.18.2022
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
from ffcuesplitter.utils import Popen, progress, frames_to_seconds

if not platform.system() == 'Windows':
    import shlex


class FFMpeg:
    """
    FFMpeg is a parent base class interface for FFCueSplitter.
    It represents FFmpeg commands and their sub-processing.
    """

    def __init__(self, **kwargs):
        """
        Constructor
        """
        self.kwargs = kwargs
        self.seconds = None
        self.arguments = None
        self.cmd = None
        self.plat = platform.system()
    # -------------------------------------------------------------#

    def arguments_building(self):
        """
        Builds `FFmpeg` arguments and calculates time seconds
        for each audio track.

        Returns:
            dict(arguments[...], seconds[...])
        """
        self.arguments = []
        self.seconds = []
        datacodecs = {'wav': ['pcm_s16le', 'wav'],
                      'wv': ['libwavpack', 'wv'],
                      'flac': ['flac', 'flac'],
                      'm4a': ['alac', 'm4a'],
                      'ogg': ['libvorbis', 'ogg'],
                      'mp3': ['libmp3lame', 'mp3'],
                      }
        codec, outext = datacodecs[self.kwargs['format']]

        for track in self.kwargs['tracks']:
            metadata = {'ARTIST': track.get('ARTIST', ''),
                        'ALBUM': track.get('ALBUM', ''),
                        'TITLE': track.get('TITLE', ''),
                        'TRACK': (str(track['TRACK']) + '/' +
                                  str(len(self.kwargs['tracks']))),
                        'GENRE': track.get('GENRE', ''),
                        'DATE': track.get('DATE', ''),
                        'COMMENT': track.get('COMMENT', ''),
                        }
            cmd = f'-i "{self.kwargs["FILE"]}"'
            cmd += f" -ss {frames_to_seconds(track['START'])}"  # conv to secs

            if 'END' in track:
                cmd += f" -to {frames_to_seconds(track['END'])}"  # to secs

            for key, val in metadata.items():
                cmd += f' -metadata {key}="{val}"'

            cmd += f' -c:a {codec}'
            cmd += f" {self.kwargs['ffmpeg_add_params']}"
            name = f"{track['TRACK']} - {track.get('TITLE', '')}.{outext}"
            cmd += f' "{os.path.join(self.kwargs["tempdir"], name)}"'
            self.arguments.append(cmd)
            self.seconds.append(track['DURATION'])

        return {'arguments': self.arguments, 'seconds': self.seconds}
    # --------------------------------------------------------------#

    def processing_with_mymet_progress(self, arguments, seconds):
        """
        FFmpeg sub-processing showing a progress indicator
        for each loop at the same line of the stdout.
        The lines shown contain percentage, size, time, bitrate
        and speed indicators.
        Also writes a log file to the same destination folder
        as the output files .

        Raises:
            FFMpegError
        Returns:
            None
        """
        args = (f'"{self.kwargs["ffmpeg_url"]}" -loglevel '
                f'{self.kwargs["ffmpeg_loglevel"]}')
        args += ' -stats -hide_banner -nostdin'
        args += f' {arguments}'
        self.cmd = args if self.plat == 'Windows' else shlex.split(args)
        if self.kwargs['dry'] is True:
            msg(self.cmd)  # print cmd in dry mode
            return
        try:
            with open(self.kwargs['logtofile'], "w", encoding='utf-8') as log:
                with Popen(self.cmd,
                           stderr=subprocess.PIPE,
                           bufsize=1,
                           universal_newlines=True) as proc:

                    for output in proc.stderr:
                        log.write(output)
                        if 'time=' in output.strip():  # ...in processing
                            prog = progress(output, round(seconds, 6))
                            sys.stdout.write(f"    {prog}\r")
                            sys.stdout.flush()

                    if proc.wait():  # error
                        raise FFMpegError(f"ffmpeg FAILED: See details: "
                                          f"'{self.kwargs['logtofile']}'"
                                          f"\nExit status: {proc.wait()}")

        except (OSError, FileNotFoundError) as excepterr:
            raise FFMpegError(excepterr) from excepterr

        except KeyboardInterrupt:
            # proc.kill()
            proc.terminate()
            sys.exit("\n[KeyboardInterrupt] FFmpeg process terminated.")
    # --------------------------------------------------------------#

    def processing_with_tqdm_progress(self, arguments, seconds):
        """
        FFmpeg sub-processing showing a tqdm progress meter
        for each loop. Also writes a log file to the same
        destination folder as the output files .
        Raises:
            FFMpegError
        Returns:
            None
        """
        args = (f'"{self.kwargs["ffmpeg_url"]}" -loglevel '
                f'{self.kwargs["ffmpeg_loglevel"]}')
        args += ' -progress pipe:1 -nostats -nostdin'
        args += f' {arguments}'
        self.cmd = args if self.plat == 'Windows' else shlex.split(args)
        if self.kwargs['dry'] is True:
            msg(self.cmd)
            return

        progbar = tqdm(total=round(seconds, 6),
                       unit="s",
                       dynamic_ncols=True
                       )
        progbar.clear()
        previous_s = 0

        try:
            with open(self.kwargs['logtofile'], "w", encoding='utf-8') as log:
                with Popen(self.cmd,
                           stdout=subprocess.PIPE,
                           stderr=log,
                           bufsize=1,
                           universal_newlines=True) as proc:

                    for output in proc.stdout:
                        if "out_time_ms" in output.strip():
                            s_processed = int(output.split('=')[1]) / 1_000_000
                            s_increase = s_processed - previous_s
                            progbar.update(s_increase)
                            previous_s = s_processed

                    if proc.wait():  # error
                        progbar.close()
                        raise FFMpegError(f"ffmpeg FAILED: See details: "
                                          f"'{self.kwargs['logtofile']}'"
                                          f"\nExit status: {proc.wait()}")

            progbar.close()

        except (OSError, FileNotFoundError) as excepterr:
            progbar.close()
            raise FFMpegError(excepterr) from excepterr

        except KeyboardInterrupt:
            # proc.kill()
            progbar.close()
            proc.terminate()
            sys.exit("\n[KeyboardInterrupt] FFmpeg process terminated.")
    # --------------------------------------------------------------#

    def processing_with_standard_progress(self, arguments, *args):
        """
        FFmpeg sub-processing with stderr output to console.
        This method prints anything depending on the loglevel
        option.
        Raises:
            FFMpegError
        Returns:
            None
        """
        args = (f'"{self.kwargs["ffmpeg_url"]}" -loglevel '
                f'{self.kwargs["ffmpeg_loglevel"]}')
        args += f' {arguments}'
        self.cmd = args if self.plat == 'Windows' else shlex.split(args)
        if self.kwargs['dry'] is True:
            msg(self.cmd)
            return
        try:
            subprocess.run(self.cmd, check=True, shell=False)

        except FileNotFoundError as err:
            raise FFMpegError(f"{err}") from err

        except subprocess.CalledProcessError as err:
            raise FFMpegError(f"ffmpeg FAILED: {err}") from err

        except KeyboardInterrupt:
            sys.exit("\n[KeyboardInterrupt]")
