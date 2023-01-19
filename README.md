# FFcuesplitter - FFmpeg based audio splitter for audio CD images supplied with .cue sheet files.

[![Image](https://img.shields.io/static/v1?label=python&logo=python&message=3.7%20|%203.8%20|%203.9%20|%203.10%20|%203.11&color=blue)](https://www.python.org/downloads/)
[![Python application](https://github.com/jeanslack/FFcuesplitter/actions/workflows/CI.yml/badge.svg)](https://github.com/jeanslack/FFcuesplitter/actions/workflows/CI.yml)

FFcuesplitter is a multi-platform CUE sheet splitter entirely based on FFmpeg.
Splits big audio tracks and automatically embeds tags using the information
contained in the associated **"CUE"** sheet. It supports multiple CUE sheet
encodings and many input formats (due to FFmpeg), including APE format, without
need installing extra audio libs and packages. It has the ability to accept both
files and directories as input while also working in recursive mode. Can be used
both as a Python module and from command line.   

## Features

- Supports many input formats.
- Convert to Wav, Flac, Ogg, Opus, and Mp3 formats.
- Ability to copy source codec and format without re-encoding.
- Batch mode processing is also available.
- Accepts both multiple CUE file names and multiple folder path names.
- Ability to activate the recursive option to search for CUE files in all subfolders.
- Optionally auto-generate audio collection folders (Artist/Album/TrackNumber - Title)
- Auto-tag from CUE file data.
- Features automatic character set detection for CUE files (via [chardet](https://pypi.org/project/chardet/)).
- Works on Linux, MacOs, FreeBSD, Windows.
- Can be used both as a Python module and in command line mode.

## Requires

- Python >=3.7
- [deflacue](https://pypi.org/project/deflacue/)
- [chardet](https://pypi.org/project/chardet/)
- [tqdm](https://pypi.org/project/tqdm/#description)
- [FFmpeg](https://ffmpeg.org/) *(including ffprobe)*


## Usage

### Using Command Line

```
ffcuesplitter -i FILENAMES DIRNAMES [FILENAMES DIRNAMES ...]
              [-r]
              [-f {wav,flac,mp3,ogg,opus,copy}]
              [-o OUTPUTDIR]
              [-c {artist+album,artist,album}]
              [-ow {ask,never,always}]
              [--ffmpeg-cmd URL]
              [--ffmpeg-loglevel {error,warning,info,verbose,debug}]
              [--ffmpeg-add-params 'parameters']
              [-p {tqdm,standard}]
              [--ffprobe-cmd URL]
              [--dry]
              [-h]
              [--version]
```

**Examples**   

`ffcuesplitter -i 'inputfile_1.cue' 'inputfile_2.cue' 'inputfile_3.cue'`   

Batch file processing to split and convert to default audio `flac` format.   

`ffcuesplitter -i '/User/music/collection/inputfile.cue' -f ogg -o 'my-awesome-tracklist'`   

To splits the individual audio tracks into `ogg` format
and saves them in the 'my-awesome-tracklist' folder.   

**For further information and other examples visit the [wiki page](https://github.com/jeanslack/FFcuesplitter/wiki)**   
***

### Using Python

```python
>>> from ffcuesplitter.cuesplitter import FFCueSplitter
```

Splittings:   

```python
>>> split = FFCueSplitter(filename='filename.cue')
>>> split.open_cuefile()
>>> split.do_operations()
```

Get data tracks and FFmpeg args:   

```python
>>> data = FFCueSplitter('filename.cue', dry=True)
>>> data.open_cuefile()
>>> data.audiotracks  # trackdata
>>> data.cue.meta.data  # cd_info
>>> data.ffmpeg_arguments()
```

For arguments meaning and more details, type `help(FFCueSplitter)`   

**For further information and other examples visit the [wiki page](https://github.com/jeanslack/FFcuesplitter/wiki)**   
***

## Installation

`python3 -m pip install ffcuesplitter`   

## License and Copyright

Copyright (C) 2023 Gianluca Pernigotto   
Author and Developer: Gianluca Pernigotto   
Mail: <jeanlucperni@gmail.com>   
License: GPL3 (see LICENSE file in the source folder)   


