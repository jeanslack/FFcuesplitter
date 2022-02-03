#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
First release: Jan 20 2022

Name: setup.py
Porpose: building ffcuesplitter sources and package
USAGE: python3 setup.py sdist bdist_wheel
Platform: Gnu/Linux-Unix-MacOs
Writer: jeanslack <jeanlucperni@gmail.com>
license: GPL3
Rev: Feb 02 2022
Code checker: flake8, pylint
####################################################################

This file is part of ffcuesplitter.

    ffcuesplitter is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    ffcuesplitter is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with ffcuesplitter.  If not, see <http://www.gnu.org/licenses/>.

"""
from setuptools import setup, find_packages
from ffcuesplitter.info import (__version__,
                                __license__,
                                __githuburl__,
                                __author__,
                                __contact__,
                                __packagename__,
                                __description__,
                                __descriptionfull__
                                )

INST_REQ = ["chardet>=4.0.0", "tqdm>=4.38.0", "deflacue>=2.0.1"]
SETUP_REQ = ["setuptools>=47.1.1",
             "wheel>=0.34.2",
             "twine>=3.1.1"
             ]

CLASSIFIERS = [
            'Development Status :: 4 - Beta',
            'Environment :: Console',
            'Intended Audience :: End Users/Desktop',
            'Intended Audience :: Developers',
            'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
            'Natural Language :: English',
            'Operating System :: Microsoft :: Windows',
            'Operating System :: MacOS :: MacOS X',
            'Operating System :: POSIX :: Linux',
            'Programming Language :: Python :: 3',
            'Programming Language :: Python :: 3.6',
            'Programming Language :: Python :: 3.7',
            'Programming Language :: Python :: 3.8',
            'Programming Language :: Python :: 3.9',
            'Topic :: Multimedia :: Sound/Audio :: Conversion',
            'Topic :: Utilities',
                ]

# get the package data
DATA_FILES = [('share/man/man1', ['man/ffcuesplitter.1.gz'])]

with open('README.md', 'r', encoding='utf8') as readme:
    long_descript = readme.read()

setup(name=__packagename__,
      version=__version__,
      description=__description__,
      long_description=long_descript,
      long_description_content_type='text/markdown',
      author=__author__,
      author_email=__contact__,
      url=__githuburl__,
      license=__license__,
      platforms=["All"],
      packages=find_packages(),
      data_files=DATA_FILES,
      zip_safe=False,
      python_requires=">=3.6",
      install_requires=INST_REQ,
      setup_requires=SETUP_REQ,
      entry_points={
          "console_scripts": ['ffcuesplitter = ffcuesplitter.main:main']},
      classifiers=CLASSIFIERS,
      )
