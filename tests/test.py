# -*- coding: UTF-8 -*-

"""
Porpose: Contains test cases for the splitcue object.
Rev: Jan.05.2022
"""
import os
import sys
import os.path
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
                     'suffix': OUTFORMAT,
                     'overwrite': OVERWRITE}

    def test_invalid_file(self):
        """
        test to assert InvalidFileError exception
        """
        fname = {'filename': '/invalid/file.cue'}

        with self.assertRaises(InvalidFileError):
            FFCueSplitter(**{**self.args, **fname})

    def test_parser_with_iso_file_encoding(self):
        """
        test cuefile parsing with ISO-8859-1 encoding
        """
        fname = {'filename': FILECUE_ISO}
        split = FFCueSplitter(**{**self.args, **fname})
        parser = split.open_cuefile()

        self.assertEqual(parser['FILE'], os.path.join(WORKDIR,
                                                      'Three Samples.flac'))
        self.assertEqual(parser['tracks'][0]['END'], 88200)
        self.assertEqual(parser['tracks'][1]['END'], 176400)
        self.assertEqual(parser['tracks'][2]['START'], 176400)
        self.assertEqual(parser['tracks'][2]['TITLE'], 'è di 500 Hz')

    def test_parser_with_ascii_file_encoding(self):
        """
        test cuefile parsing with ASCII encoding
        """
        fname = {'filename': FILECUE_ASCII}
        split = FFCueSplitter(**{**self.args, **fname})
        parser = split.open_cuefile()

        self.assertEqual(parser['outputdir'], WORKDIR)
        self.assertEqual(parser['tracks'][0]['START'], 0)
        self.assertEqual(parser['tracks'][1]['START'], 88200)
        self.assertEqual(parser['tracks'][2]['DURATION'], 2.0)
        self.assertEqual(parser['tracks'][2]['ALBUM'], 'Sox - Three samples')


class FFmpegCommandsTestCase(unittest.TestCase):
    """
    Test case to get data from cue sheet file
    """
    def setUp(self):
        """
        Method called to prepare the test fixture
        """
        self.args = {'outputdir': os.path.dirname(FILECUE_ISO),
                     'suffix': OUTFORMAT,
                     'overwrite': OVERWRITE,
                     'dry': True
                     }

    def test_ffmpeg_commands(self):
        """
        test cuefile parsing with ASCII encoding
        """
        fname = {'filename': FILECUE_ASCII}
        split = FFCueSplitter(**{**self.args, **fname})
        split.open_cuefile()
        ret = split.do_operations()

        self.assertEqual(ret, None)


def main():
    """
    Run
    """
    unittest.main()


if __name__ == '__main__':
    main()
