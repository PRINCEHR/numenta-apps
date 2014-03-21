#-------------------------------------------------------------------------------
# Copyright (C) 2013-2014 Numenta Inc. All rights reserved.
#
# The information and source code contained herein is the
# exclusive property of Numenta Inc.  No part of this software
# may be used, reproduced, stored or distributed in any form,
# without explicit written authorization from Numenta Inc.
#-------------------------------------------------------------------------------
"""
  Grok CLI
  ========

  Included in the Grok CLI package is a `grok` console script, and a reusable
  `grokcli` Python package.  See README.md for usage and additional details.

  Installation notes
  ------------------

  This file (setup.py) is provided to support installation using the native
  python setuptools-based ecosystem, including PyPi, `easy_install` and `pip`.

  Disclaimer:  Your specific environment _may_ require additional arguments to
  pip, setup.py and easy_install such as `--root`, `--install-option`,
  `--script-dir`, `--script-dir`, or you may use `sudo` to install at the system
  level.

  Building source distribution for release
  ----------------------------------------

  The source distribution package is built using the `sdist build` sub-command:

      python setup.py sdist build

  Resulting in the creation of dist/grokcli-1.0.tar.gz, which will be uploaded
  to PyPi (or another distribution channel).  The grokcli package can be
  installed from the tarball directly using a number of approaches:

      pip install grokcli-1.0.tar.gz
      easy_install grokcli-1.0.tar.gz

  Or, by using setup.py:

      tar xzvf grokcli-1.0.tar.gz
      cd grokcli-1.0.tar.gz
      python setup.py install

  Once uploaded to PyPi, grokcli can be installed by name:

      pip install grokcli
      easy_install grokcli

  Alternate installation by `pip wheel`
  -------------------------------------

  Recently, pip has added a new binary distribution format "wheel", which
  simplifies the process somewhat.

  To create a wheel:

      pip wheel .

  Resulting in the creation of wheelhouse/grokcli-1.0-py27-none-any.whl along
  with a few other .whl files related to grokcli dependencies.

  To install from cached wheel:

      pip install --use-wheel --no-index --find-links=wheelhouse/ wheelhouse/grokcli-1.0-py27-none-any.whl

  Or, from PyPi, assuming the wheels have been uploaded to PyPi:

      pip install --use-wheel grokcli
"""
import sys
from setuptools import find_packages, setup



def printTerms():
  print("\nBy using the Grok CLI, you agree to terms and conditions\n"
        "outlined in the product End User License Agreement (EULA):\n"
        "https://aws.amazon.com/marketplace/agreement?asin=B00I18SNQ6\n")


def printRegisterHint():
  print("If you haven't already registered, please do so by visiting\n"
        "the URL: GROK_SERVER/grok/register, to help us serve you better.\n")



requirements = map(str.strip, open("requirements.txt").readlines())

version = {}
execfile("grokcli/__version__.py", {}, version)

setup(
  name = "grokcli",
  description = "Grok Command Line Interface",
  classifiers = [
    "Development Status :: 5 - Production/Stable",
    "Environment :: Console",
    "Intended Audience :: Developers",
    "Intended Audience :: Information Technology",
    "License :: OSI Approved :: Apache Software License",
    "Programming Language :: Python :: 2",
    "Topic :: Utilities"],
  keywords = "grok, numenta, anomaly detection, monitoring",
  author = "Austin Marshall, Chetan Surpur",
  author_email = "amarshall@numenta.com, csurpur@numenta.com",
  packages = find_packages(),
  entry_points = {"console_scripts": ["grok = grokcli:main"]},
  install_requires = requirements,
  extras_require = {"docs": ["sphinx"]},
  version = version["__version__"]
)

if "sdist" not in sys.argv:
  # Don't print terms or registration hint when building Python distribution
  printTerms()
  printRegisterHint()
