# FFcuesplitter - FFmpeg based audio splitter for audio CD images supplied with .cue sheet files.

FFcuesplitter is a multi-platform CUE sheet splitter entirely based on FFmpeg. 
Accurately splits big audio tracks and automatically tags them using the information 
contained in the associated **"CUE"** sheet. It supports many input formats (due to FFmpeg), 
including APE format, and no need installing third-party libs or packages. It can 
support multiple CUE sheet encodings via chardet library. Can be used both as a Python 
module (API) and in command line mode.   

# Features

- It supports many input formats
- Supported formats to output: wav, wv, flac, m4a, ogg, mp3
- Ability to Auto-tag from .cue file data.
- Supports multiple .cue file encoding via chardet package.
- It plans to work on Linux, MacOs, FreeBSD and Windows.
- Can be used both as a Python module and in command line mode.

## Requires

- Python >=3.6
- [chardet](https://pypi.org/project/chardet/) (The Universal Character Encoding Detector)
- [tqdm](https://pypi.org/project/tqdm/#description) (Fast, Extensible Progress Meter)
- [FFmpeg](https://ffmpeg.org/) *(including ffprobe)*

 
Ubuntu users can install required dependencies like this:   
`sudo apt install ffmpeg python3-chardet python3-tqdm`   

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
             [-p {tqdm,mymet,standard}]
             [--ffprobe_url URL] 
             [--dry]

```

#### Examples

`ffcuesplitter -i 'inputfile.cue'`   

To split and convert several audio formats into the relative individual 
`flac` format audio tracks.    

`ffcuesplitter -i '/User/music/collection/inputfile.cue' -f wav -o 'my-awesome-tracklist'`   

To splits the individual audio tracks into `wav` format 
and saves them in the 'my-awesome-tracklist' folder.   

### From Python Interpreter

```python
>>> from ffcuesplitter.cuesplitter import FFCueSplitter
>>> split = FFCueSplitter(filename='/home/user/my_file.cue')
>>> split.open_cuefile()
>>> split.do_operations()
```

For a more advanced use of this class do not use `do_operations` method as it 
automates all operations. The following example is suggested:   

```python
>>> from ffcuesplitter.cuesplitter import FFCueSplitter
>>> split = FFCueSplitter(filename='/home/user/my_file.cue')
>>> split.open_cuefile()
>>> split.kwargs['tempdir'] = '/tmp/mytempdir'
>>> ffmpeg_args = split.arguments_building()
>>> for args, secs in zip(split.arguments, split.seconds):
...     split.processing_with_tqdm_progress(args, secs)
>>> split.move_files_on_outputdir()
```

More details are described in the `__doc__` strings of `FFCueSplitter` class or by typing 
`help(FFCueSplitter)` in the Python console, or by reading the **ffcuesplitter manual page**.

## Installation

`python3 -m pip install ffcuesplitter`

## License and Copyright

Copyright © 2022 Gianluca Pernigotto   
Author and Developer: Gianluca Pernigotto   
Mail: <jeanlucperni@gmail.com>   
License: GPL3 (see LICENSE file in the docs folder)


