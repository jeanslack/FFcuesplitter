# FFcuesplitter - FFmpeg based audio splitter for audio CD images with .cue sheet files.

FFcuesplitter is a multi-platform cue sheet splitter entirely based on FFmpeg.
Accurately splits big audio tracks and automatically tags them using the information 
contained in the associated **"CUE"** sheet file. It can handle multiple CUE sheet 
files encodings via chardet library.    

# Features

- Supported input formats: Many, all supported by FFmpeg.
- Supported output formats: wav, wv, flac, m4a, ogg, mp3
- Auto-tag from .cue file data.
- It supports additionals parameters for FFmpeg.
- Can be used both as a Python module and in command line mode.

## Requires

- Python >=3.6
- [chardet](https://pypi.org/project/chardet/) (The Universal Character Encoding Detector)
- [FFmpeg](https://ffmpeg.org/) *(including ffprobe)*

 
Ubuntu users can install required dependencies like this:   
`sudo apt install ffmpeg python3-chardet`   

## Usage

### From Command Line

```
ffcuesplitter -i IMPUTFILE
             [-h] 
             [--version] 
             [-f {wav,wv,flac,mp3,ogg,m4a}] 
             [-o OUTPUTDIR]
             [-ow {ask,never,always}] 
             [--ffmpeg_url URL]
             [--ffmpeg_loglevel {error,warning,info,verbose,debug}]
             [--ffmpeg_add_params 'PARAMS ...'] 
             [--ffprobe_url URL] 
             [--dry]

```

#### Examples

`ffcuesplitter -i 'inputfile.cue'`   

To split and convert several audio formats into the relative individual 
`flac` format audio tracks.    

`ffcuesplitter -i '/User/music/collection/inputfile.cue' -f wav -o 'my-awesome-tracklist'`   

This command splits the individual audio tracks into `wav` format 
and saves them in the 'my-awesome-tracklist' folder.   

### From Python Interpreter

```python
>>> from ffcuesplitter.cuesplitter import FFCueSplitter
>>> split = FFCueSplitter(filename='/home/user/my_file.cue')
>>> split.open_cuefile()
>>> split.do_operations()
```

For a more advanced use the following examples are suggested:   

```python
>>> from ffcuesplitter.cuesplitter import FFCueSplitter
>>> split = FFCueSplitter(filename='/home/user/my_file.cue',
                          outputdir='/home/user',
                          suffix='flac',
                          overwrite='ask',
                          ffmpeg_url='ffmpeg',
                          ffmpeg_loglevel='warning',
                          ffprobe_url='ffprobe',
                          ffmpeg_add_params='-compression_level 8',
                          dry=False
                          )
>>> split.open_cuefile()
>>> split.kwargs['tempdir'] = '/tmp/mytempdir'
>>> commands, durations = split.command_building()
>>> with open(logpath, 'w', encoding='utf-8') as split.logfile:
...     for cmd, dur in zip(commands, durations):
...         split.run(cmd, dur)
>>> split.move_files_on_outputdir()
```

## Installation

`python3 -m pip install ffcuesplitter`

## License and Copyright

Copyright © 2022 Gianluca Pernigotto   
Author and Developer: Gianluca Pernigotto   
Mail: <jeanlucperni@gmail.com>   
License: GPL3 (see LICENSE file in the docs folder)


