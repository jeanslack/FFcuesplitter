# FFcuesplitter - FFmpeg based audio splitter for audio CD images supplied with .cue sheet files.

FFcuesplitter is a multi-platform CUE sheet splitter entirely based on FFmpeg. 
Splits big audio tracks and automatically embeds tags using the information 
contained in the associated **"CUE"** sheet. It supports many input formats 
(due to FFmpeg), including APE format, without need installing extra audio libs 
or packages. automatically support multiple CUE sheet encodings. Can be used both 
as a Python module (API) and in command line mode.   

# Features

- It supports many input formats.
- Supported formats to output: wav, flac, ogg, mp3.
- Ability to copy codec without re-encoding.
- Auto-tag from .cue file data.
- Supports multiple .cue file encodings.
- Works on Linux, MacOs, FreeBSD, Windows.
- Can be used both as a Python module and in command line mode.

## Requires

- Python >=3.6
- [deflacue](https://pypi.org/project/deflacue/)
- [chardet](https://pypi.org/project/chardet/)
- [tqdm](https://pypi.org/project/tqdm/#description)
- [FFmpeg](https://ffmpeg.org/) *(including ffprobe)*


## Usage

### From Command Line

```
ffcuesplitter -i IMPUTFILE
             [-h] 
             [--version] 
             [-f {wav,flac,mp3,ogg,copy}] 
             [-o OUTPUTDIR]
             [-ow {ask,never,always}] 
             [--ffmpeg_cmd URL]
             [--ffmpeg_loglevel {error,warning,info,verbose,debug}]
             [--ffmpeg_add_params 'PARAMS ...'] 
             [-p {tqdm,mymet,standard}]
             [--ffprobe_cmd URL] 
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
```

Splittings:   

```python
>>> split = FFCueSplitter(filename='/home/user/my_file.cue')
>>> split.open_cuefile()
>>> split.do_operations()
```

Get data tracks and FFmpeg args:   

```python
>>> data = FFCueSplitter('/home/user/other.cue', dry=True)
>>> data.open_cuefile()
>>> data.audiotracks  # trackdata
>>> data.cue.meta.data  # cd_info
>>> data.ffmpeg_arguments()
```

Only processing one track:   

```python
>>> f = FFCueSplitter('/home/user/my_file.cue', progress_meter='tqdm')
>>> f.open_cuefile()
>>> f.kwargs['tempdir'] = '/tmp/mytempdir'
>>> f.ffmpeg_arguments()
>>> f.processing(myfile.arguments[2], myfile.seconds[2])  # track three
>>> f.move_files_to_outputdir()
```

More details are described in the `__doc__` strings of `FFCueSplitter` class or by typing 
`help(FFCueSplitter)` in the Python console, or by reading the **ffcuesplitter man page**.

## Installation

`python3 -m pip install ffcuesplitter`

## License and Copyright

Copyright © 2022 Gianluca Pernigotto   
Author and Developer: Gianluca Pernigotto   
Mail: <jeanlucperni@gmail.com>   
License: GPL3 (see LICENSE file in the docs folder)


