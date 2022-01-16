# FFcuesplitter - FFmpeg based audio splitter for .cue sheet files.

FFcuesplitter is a multi-platform cue sheet splitter entirely based on FFmpeg.
It splits big audio tracks and automatically tags them using the information 
contained in the associated **"CUE"** sheet file. It can handle multiple CUE sheet 
files encodings via chardet library.    

# Features

- Supported input formats: Many, all supported by FFmpeg.
- Supported encoders for output: pcm_s16le, libwavpack, flac, alac, libvorbis, libmp3lame
- Supported output formats: wav, wv, flac, m4a, ogg, mp3
- Auto-tag is supported for all output formats.
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
>>> kwargs = {'filename': '/home/user/my_file.cue',
              'outputdir': '/home/user/some_other_dir',
              'format': 'flac',
              'overwrite': 'ask'
              'ffmpeg_url': '/usr/bin/ffmpeg',
              'ffprobe_url': '/usr/bin/ffprobe',
             }
>>> split = FFCueSplitter(**kwargs)
>>> split.open_cuefile()
>>> split.do_operations()
```

## Installation

`python3 -m pip install ffcuesplitter`

## License and Copyright

Copyright © 2022 Gianluca Pernigotto   
Author and Developer: Gianluca Pernigotto   
Mail: <jeanlucperni@gmail.com>   
License: GPL3 (see LICENSE file in the docs folder)


