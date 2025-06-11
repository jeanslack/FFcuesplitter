"""
First release: January 28 2023

Name: user_service.py
Porpose: Services for the end user.
Platform: all
Writer: jeanslack <jeanlucperni@gmail.com>
license: GPL3
Copyleft: (C) 2025 Gianluca Pernigotto <jeanlucperni@gmail.com>
Rev: June 10 2025
Code checker: flake8, pylint
####################################################################

This file is part of FFcuesplitter.

    FFcuesplitter is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    FFcuesplitter is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with FFcuesplitter.  If not, see <http://www.gnu.org/licenses/>.
"""
import os
import shutil
import tempfile
import logging
from ffcuesplitter.cuesplitter import FFCueSplitter
from ffcuesplitter.exceptions import FFCueSplitterError


class FileSystemOperations(FFCueSplitter):
    """
    This is a subclass derived from the `FFCueSplitter` class.
    It implements a convenient interface for file system
    operations, such as overwrite checking functionality for
    file destinations, writing files in a temporary context,
    move files from temporary directory to output directory.
    There is also a specific method for dry mode.

    USAGE:
        >>> from ffcuesplitter.user_service import FileSystemOperations
        >>> split = FileSystemOperations(**kwargs)
        >>> if split.kwargs['dry']:
        >>>     split.dry_run_mode()
        >>> else:
        >>>     overw = split.check_for_overwriting()
        >>>     if not overw:
        >>>         split.work_on_temporary_directory()

    For the arguments meaning see `FFCueSplitter` class
    of the `cuesplitter` module on `ffcuesplitter` package.

    Also, visit the wiki page at:
    https://github.com/jeanslack/FFcuesplitter/wiki/Usage-from-Python
    """
    # ----------------------------------------------------------------#

    def remove_source_file(self):
        """
        Remove the CUE file and the original audio file
        from the filesystem. If either one is missing, no
        deletion will be applied.
        Return True if deletion was successfull, False otherwise.
        """
        cuef = self.kwargs['filename']
        audf = self.audiosource
        exist = False
        if os.path.exists(cuef) and os.path.exists(audf):
            if os.path.isfile(cuef) and os.path.isfile(audf):
                exist = True
                logging.info("Deleting CUE file: '%s'", cuef)
                os.remove(cuef)
                logging.info("Deleting audio source file: '%s'", audf)
                os.remove(audf)
        if not exist:
            logging.warning("File deletion failed, source files are missing")
            return exist
        return exist
    # ----------------------------------------------------------------#

    def dry_run_mode(self):
        """
        lists recipes in dry run mode.
        """
        self.kwargs['tempdir'] = self.kwargs['outputdir']
        recipes = self.commandargs(self.audiotracks)
        for args in recipes['recipes']:
            msg = f'{args[0]}\n'
            logging.info(msg)
    # ----------------------------------------------------------------#

    def check_for_overwriting(self):
        """
        Checking user options for overwriting files.
        """
        outputdir = self.kwargs['outputdir']
        overwr = self.kwargs['overwrite']
        tracks = self.audiotracks.copy()

        if overwr == 'always':
            logging.info("Overwrite existing file because "
                         "you specified the 'always' option")
            return False

        if overwr == 'never':
            logging.info("Do not overwrite any files because "
                         "you specified 'never' option")
            return True

        for data in tracks:  # self.audiotracks
            track = (f"{str(data['TRACK_NUM']).rjust(2, '0')} - "
                     f"{data['FILE_TITLE']}.{self.kwargs['outputformat']}")
            pathfile = os.path.join(outputdir, track)

            if os.path.exists(pathfile):
                if overwr in ('n', 'N', 'y', 'Y', 'ask'):
                    while True:
                        logging.warning("File already exists: '%s'",
                                        os.path.join(outputdir, track))
                        overwr = input("\033[33;1mOverwrite? "
                                       "[Y/n/always/never]\033[0m > ")
                        if overwr in ('Y', 'y', 'n', 'N', 'always', 'never'):
                            break
                        logging.error("Invalid option '%s'", overwr)
                        continue
                if overwr == 'never':
                    logging.info("Do not overwrite any files because "
                                 "you specified 'never' option")
                    return True

            if overwr in ('n', 'N'):
                del self.audiotracks[self.audiotracks.index(data)]

            elif overwr in ('y', 'Y', 'always', 'never', 'ask'):
                if overwr == 'always':
                    logging.info("Overwrite existing file because "
                                 "you specified the 'always' option")
                    return False
        return False
    # ----------------------------------------------------------------#

    def move_files_to_outputdir(self):
        """
        All files are processed in a /temp dir. After the split
        operation is complete, all tracks are moved from /temp dir
        to output dir.

        Raises:
            FFCueSplitterError
        Returns:
            None

        """
        logging.info("Move files to: '%s'",
                     os.path.abspath(self.kwargs['outputdir']))
        outputdir = self.kwargs['outputdir']

        for track in os.listdir(self.kwargs['tempdir']):
            try:
                shutil.move(os.path.join(self.kwargs['tempdir'], track),
                            os.path.join(outputdir, track))
            except Exception as error:
                raise FFCueSplitterError(error) from error
    # ----------------------------------------------------------------#

    def work_on_temporary_directory(self):
        """
        Automates the work in a temporary context using tempfile.

        Raises:
            FFCueSplitterError
        Returns:
            None

        """
        if not self.audiotracks:
            raise FFCueSplitterError('No audio tracks')

        with tempfile.TemporaryDirectory(suffix=None,
                                         prefix='ffcuesplitter_',
                                         dir=None) as tmpdir:
            self.kwargs['tempdir'] = tmpdir
            recipes = self.commandargs(self.audiotracks)

            logging.info("Temporary Target: '%s'", self.kwargs['tempdir'])
            logging.info("Extracting audio tracks (type Ctrl+c to stop):")

            count = 0
            lengh = len(recipes['recipes'])
            for args in recipes['recipes']:
                count += 1
                msg = (f'Write Track {count}/{lengh} >> '
                       f'"{args[1]["titletrack"]}" ...')
                logging.info(msg)
                self.command_runner(args[0], args[1]['duration'])

            logging.info("...done exctracting")
            # You must move the files from within the temporary context
            self.move_files_to_outputdir()
            # remove source file if `del_orig_files` argument is given.
            if self.kwargs['del_orig_files']:
                self.remove_source_file()
# ------------------------------------------------------------------------


class FileFinder:
    """
    Finds and collect files based on one or more suffixes in
    a given pathnames list. Features methods for recursive and
    non-recursive searching.

    Constructor:

        ff = FileFinder(target=str('pathnames'))
        or
        ff = FileFinder(target=list('pathnames',))

    Available methods:

        - find_files(suffix=str or list of ('.suffix',))
        - find_files_recursively(suffix=str or list of ('.suffix',))

    Always returns a dictionary with three keys:
    `FOUND`, `DISCARDED`, `INEXISTENT` with lists as values.

    If filenames are given instead of dirnames, they will be
    returned with the `DISCARDED` key. If non-existent filenames
    or dirnames are given, they will be returned with the
    `INEXISTENT` key. All files found will be returned with
    the FOUND key.

    """
    def __init__(self, target: str = ''):
        """
        target: Expects a str('pathdir') or a list of ('pathdirs',)

        """
        self.filtered = None
        self.rejected = None  # add here only if it's file
        self.nonexistent = None
        self.target = tuple((target,)) if isinstance(target, str) else target
    # -------------------------------------------------------------#

    def find_files_recursively(self, suffix: str = '') -> dict:
        """
        find files in recursive mode.
        suffix: Expects a str(.suffix) or a list of (.suffixes,)
        Returns: dict

        """
        self.filtered = []
        self.rejected = []  # add here only if it's file
        self.nonexistent = []
        suffix = tuple((suffix,)) if isinstance(suffix, str) else suffix

        fileswalk = {}
        for dirs in self.target:
            if os.path.exists(dirs):
                if os.path.isdir(dirs):
                    for root, alldirs, allfiles in os.walk(dirs):
                        fileswalk[root] = list(alldirs + allfiles)
                else:
                    self.rejected.append(dirs)  # only existing files
            else:
                self.nonexistent.append(dirs)  # all non-existing files/dirs
        for path, name in fileswalk.items():
            for files in name:
                if os.path.splitext(files)[1] in suffix:
                    self.filtered.append(os.path.join(path, files))

        return {"FOUND": self.filtered,
                "DISCARDED": self.rejected,
                "INEXISTENT": self.nonexistent
                }
    # -------------------------------------------------------------#

    def find_files(self, suffix: str = '') -> dict:
        """
        find files in non-recursive mode.
        suffix: Expects a str(.suffix) or a list of (.suffixes,)
        Returns: dict

        """
        self.filtered = []
        self.rejected = []  # add here only if it's file
        self.nonexistent = []
        suffix = tuple((suffix,)) if isinstance(suffix, str) else suffix

        for dirs in self.target:
            if os.path.exists(dirs):
                if os.path.isdir(dirs):
                    for files in os.listdir(dirs):
                        if os.path.splitext(files)[1] in suffix:
                            self.filtered.append(os.path.join(dirs, files))
                else:
                    self.rejected.append(dirs)  # only existing files
            else:
                self.nonexistent.append(dirs)  # all non-existing files/dirs

        return {"FOUND": self.filtered,
                "DISCARDED": self.rejected,
                "INEXISTENT": self.nonexistent
                }
# ------------------------------------------------------------------------
