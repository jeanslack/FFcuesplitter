# FFcuesplitter - FFmpeg based audio splitter for audio CD images supplied with .cue sheet files.

FFcuesplitter is a multi-platform CUE sheet splitter entirely based on FFmpeg. 
Splits big audio tracks and automatically tags them using the information 
contained in the associated **"CUE"** sheet. It supports many input formats 
(due to FFmpeg), including APE format without need installing third-party libs 
or packages. automatically support multiple CUE sheet encodings via chardet, deflacue 
libraries. Can be used both as a Python module (API) and in command line mode.   

# Features

- It supports many input formats
- Supported formats to output: wav, flac, ogg, mp3
- Ability to Auto-tag from .cue file data.
- Supports multiple .cue file encodings.
- It plans to work on Linux, MacOs, FreeBSD and Windows.
- Can be used both as a Python module and in command line mode.

## Requires

- Python >=3.6
- [deflacue](https://pypi.org/project/deflacue/)
- [chardet](https://pypi.org/project/chardet/)
- [tqdm](https://pypi.org/project/tqdm/#description)
- [FFmpeg](https://ffmpeg.org/) *(including ffprobe)*

 
Ubuntu users can install required dependencies like this:   
`sudo apt install ffmpeg python3-chardet python3-tqdm`   

## Usage

### From Command Line

```
ffcuesplitter -i IMPUTFILE
             [-h] 
             [--version] 
             [-f {wav,flac,mp3,ogg}] 
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
```

Splittings:   

```python
>>> split = FFCueSplitter(filename='/home/user/my_file.cue')
>>> split.open_cuefile()
>>> split.do_operations()
```

Get data tracks:   

```python
>>> data = FFCueSplitter(filename='/home/user/other.cue', dry=True)
>>> data.open_cuefile()
>>> trackdata = data.audiotraks
>>> cd_info = data.cue.meta.data
>>> data.kwargs['tempdir'] = '.'
>>> ffmpeg_args = data.ffmpeg_arguments()
```

Only processing some file:   

```python
>>> myfile = FFCueSplitter(filename='/home/user/my_file.cue', progress_meter='tqdm')
>>> myfile.open_cuefile()
>>> myfile.kwargs['tempdir'] = '/tmp/mytempdir'
>>> myfile.ffmpeg_arguments()
>>> myfile.processing(myfile.arguments[2], myfile.seconds[2])
>>> myfile.move_files_on_outputdir()
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


