# -*- coding: UTF-8 -*-

"""
Porpose: Contains test cases for the FFCueSplitter object.
Rev: Feb 06 2023
"""
import os
import sys
import unittest


PATH = os.path.realpath(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(PATH)))

try:
    from ffcuesplitter.cuesplitter import FFCueSplitter
    from ffcuesplitter.exceptions import InvalidFileError

except ImportError as error:
    sys.exit(error)

WORKDIR = os.path.dirname(PATH)
FILECUE_ASCII = os.path.join(WORKDIR, 'Three Samples_ASCII.cue')
FILECUE_ISO = os.path.join(WORKDIR, 'Three Samples_ISO-8859-1.cue')
OUTFORMAT = 'flac'
OVERWRITE = "always"


class ParserCueSheetTestCase(unittest.TestCase):
    """
    Test case to get data from cue sheet file
    """
    def setUp(self):
        """
        Method called to prepare the test fixture
        """
        self.args = {'outputdir': os.path.dirname(FILECUE_ISO),
                     'outputformat': OUTFORMAT,
                     'overwrite': OVERWRITE,
                     'testpatch': True,
                     }

    def test_invalid_file(self):
        """
        test to assert InvalidFileError exception
        """
        fname = {'filename': '/invalid/file.cue'}

        with self.assertRaises(InvalidFileError):
            FFCueSplitter(**{**self.args, **fname})

    def test_tracks_with_iso_file_encoding(self):
        """
        test cuefile parsing with ISO-8859-1 encoding
        """
        args = {'filename': FILECUE_ISO, 'characters_encoding': 'ISO-8859-1'}
        split = FFCueSplitter(**{**self.args, **args})
        tracks = split.audiotracks

        self.assertEqual(tracks[0]['FILE'], 'Three Samples.flac')
        self.assertEqual(tracks[0]['END'], 88200)
        self.assertEqual(tracks[1]['END'], 176400)
        self.assertEqual(tracks[2]['START'], 176400)
        self.assertEqual(tracks[2]['TITLE'], ('500 Hz, ISO-8859-1 '
                                              '(è, é, ì, ò, à, ç, °)')
                        )

    def test_tracks_with_ascii_file_encoding(self):
        """
        test cuefile parsing with ASCII encoding
        """
        fname = {'filename': FILECUE_ASCII, 'characters_encoding': 'utf-8'}
        split = FFCueSplitter(**{**self.args, **fname})
        tracks = split.audiotracks

        self.assertEqual(tracks[0]['START'], 0)
        self.assertEqual(tracks[1]['START'], 88200)
        self.assertEqual(tracks[2]['DURATION'], 2.0)
        self.assertEqual(tracks[2]['ALBUM'], 'Test Samples ASCII')


class FFmpegArgumentsTestCase(unittest.TestCase):
    """
    Test case to get data from FFmpeg arguments building
    """
    def setUp(self):
        """
        Method called to prepare the test fixture
        """
        self.args = {'outputdir': os.path.dirname(FILECUE_ISO),
                     'outputformat': OUTFORMAT,
                     'overwrite': OVERWRITE,
                     'dry': True,
                     'testpatch': True,
                     'characters_encoding': 'utf-8',
                     }

    def test_ffmpeg_arguments(self):
        """
        test argument strings and titletrack names
        """
        fname = {'filename': FILECUE_ASCII}
        split = FFCueSplitter(**{**self.args, **fname})
        split.kwargs['tempdir'] = os.path.abspath('.')
        tracks = split.audiotracks
        data = split.commandargs(tracks)
        self.assertEqual(data['recipes'][0][0].split()[0], '"ffmpeg"')
        self.assertEqual(data['recipes'][0][1]['titletrack'],
                         '01 - 300 Hz, ASCII.flac')
        self.assertEqual(data['recipes'][1][1]['titletrack'],
                         '02 - 400 Hz, ASCII.flac')
        self.assertEqual(data['recipes'][2][1]['titletrack'],
                         '03 - 500 Hz, ASCII (è, é, ì, ò, à, ç, °).flac')

    def test_track_durations(self):
        """
        test durations of the tracks in seconds
        """
        fname = {'filename': FILECUE_ASCII}
        split = FFCueSplitter(**{**self.args, **fname})
        split.kwargs['tempdir'] = os.path.abspath('.')
        tracks = split.audiotracks
        data = split.commandargs(tracks)
        self.assertEqual(data['recipes'][0][1]['duration'], 2.0)
        self.assertEqual(data['recipes'][1][1]['duration'], 2.0)
        self.assertEqual(data['recipes'][2][1]['duration'], 2.0)


def main():
    """
    Run
    """
    unittest.main()


if __name__ == '__main__':
    main()
