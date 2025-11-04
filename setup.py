#! /usr/bin/env python3

# coding: utf-8
# /*##########################################################################
#
# Copyright (c) 2016-2019 European Synchrotron Radiation Facility
# Copyright (c) 2019-2020 Lawrence Berkeley National Laboratory
# Copyright (c) 2020-now European Synchrotron Radiation Facility
# Copyright (c) 2023-now Argonne National Laboratory
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
# ###########################################################################*/

#
# Memorandum: 
#
# Install from sources: 
#     git clone https://github.com/srio/oasys2-shadow4
#     cd oasys2-shadow4
#     python -m pip install -e . --no-deps --no-binary :all:
#
# Upload to pypi (when uploading, increment the version number):
#     python setup.py register (only once, not longer needed)
#     python setup.py sdist
#     python setup.py upload
#          
# Install from pypi:
#     pip install <name>
#

__authors__ = ["M Sanchez del Rio, Luca Rebuffi"]
__license__ = "BSD3"
__date__ = "25/10/2019"

import os
import sys
from setuptools import find_packages, setup

NAME = 'OASYS2-SHADOW4'
VERSION = '0.0.20'
ISRELEASED = False

DESCRIPTION = 'oasys2-shadow4: Oasys 2 widgets for shadow4'
README_FILE = os.path.join(os.path.dirname(__file__), 'README.md')
LONG_DESCRIPTION = open(README_FILE).read()
AUTHOR = 'M. Sanchez del Rio, L. Rebuffi'
AUTHOR_EMAIL = 'srio@esrf.eu'
URL = 'https://github.com/oasys-kit/OASYS2-SHADOW4'
DOWNLOAD_URL = 'https://github.com/oasys-kit/OASYS2-SHADOW4'
LICENSE = 'BSD3'

KEYWORDS = [
    'ray tracing',
    'x-ray optics',
    'oasys2',
    ]

CLASSIFIERS = [
    'Development Status :: 4 - Beta',
    'Environment :: X11 Applications :: Qt',
    'Environment :: Console',
    'Environment :: Plugins',
    'Programming Language :: Python',
    'Programming Language :: Python :: 3',
    'Intended Audience :: Science/Research',
    ]


SETUP_REQUIRES = (
                  'setuptools',
                  )

INSTALL_REQUIRES = (
    'oasys2>=0.0.22',
    'shadow4>=0.1.69',
    'xoppylib>=1.0.46', # used in Bragg preprocessor... todo: maybe move that part to crystalpy?
)

PACKAGES = find_packages(exclude=('*.tests', '*.tests.*', 'tests.*', 'tests'))

PACKAGE_DATA = {
    "orangecontrib.shadow4.widgets.sources":["icons/*.png", "icons/*.jpg"],
    "orangecontrib.shadow4.widgets.optics": ["icons/*.png", "icons/*.jpg"],
    "orangecontrib.shadow4.widgets.preprocessors": ["icons/*.png", "icons/*.jpg"],
    "orangecontrib.shadow4.widgets.loops":["icons/*.png", "icons/*.jpg"],
    "orangecontrib.shadow4.widgets.tools":["icons/*.png", "icons/*.jpg"],
    }

ENTRY_POINTS = {
    'oasys2.addons' : ("SHADOW4 = orangecontrib.shadow4", ),
    'oasys2.widgets' : (
            "SHADOW4 Sources = orangecontrib.shadow4.widgets.sources",
            "SHADOW4 Optics = orangecontrib.shadow4.widgets.optics",
            "SHADOW4 Preprocessors = orangecontrib.shadow4.widgets.preprocessors",
            "SHADOW4 Loops = orangecontrib.shadow4.widgets.loops",
            "SHADOW4 Tools = orangecontrib.shadow4.widgets.tools",
    ),
    'oasys2.menus' : ("shadow4menu = orangecontrib.shadow4.menu",)
    }

if __name__ == '__main__':
    setup(
          name = NAME,
          version = VERSION,
          description = DESCRIPTION,
          long_description = LONG_DESCRIPTION,
          long_description_content_type='text/markdown',
          author = AUTHOR,
          author_email = AUTHOR_EMAIL,
          url = URL,
          download_url = DOWNLOAD_URL,
          license = LICENSE,
          keywords = KEYWORDS,
          classifiers = CLASSIFIERS,
          packages = PACKAGES,
          package_data = PACKAGE_DATA,
          setup_requires = SETUP_REQUIRES,
          install_requires = INSTALL_REQUIRES,
          entry_points = ENTRY_POINTS,
          include_package_data = True,
          zip_safe = False,
          )
