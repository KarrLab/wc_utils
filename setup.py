"""A setuptools based setup module, template copied from https://github.com/pypa/sampleproject

See also:
https://packaging.python.org/en/latest/distributing.html
"""

from setuptools import setup, find_packages
from codecs import open
from os import path
from wc_utils.util.install import parse_requirements, install_dependencies
import re
import os
import wc_utils

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# parse dependencies and links from requirements.txt files
with open('requirements.txt', 'r') as file:
    install_requires, dependency_links_install = parse_requirements(file.readlines())
with open('tests/requirements.txt', 'r') as file:
    tests_require, dependency_links_tests = parse_requirements(file.readlines())
dependency_links = list(set(dependency_links_install + dependency_links_tests))

# find needed pygit2 version
libgit2_path = os.getenv("LIBGIT2")
if not libgit2_path:
    if os.name == 'nt':
        libgit2_path = os.path.join(os.getenv("ProgramFiles"), 'libgit2')
    else:
        libgit2_path = '/usr/local'
version_filename = os.path.join(libgit2_path, 'include', 'git2', 'version.h')

libgit2_version = None
with open(version_filename, 'r') as file:
    for line in file:
        match = re.findall('define *LIBGIT2_VERSION *"(.*?)"', line.strip())
        if match:
            libgit2_version = match[0]
            break

if not libgit2_version:
    raise Exception(('wc_utils requires libgit2. Please install libgit2 and then retry installing '
                     'wc_utils. Please see https://libgit2.github.com for installation instructions.'))

i_pygit2 = install_requires.index('pygit2')
install_requires[i_pygit2] = 'pygit2<={}'.format(libgit2_version)

# install non-PyPI dependencies
install_dependencies(dependency_links)

# install package
setup(
    name='wc_utils',
    version=wc_utils.__version__,

    description='Utilities for whole-cell modeling',
    long_description=long_description,

    # The project's main homepage.
    url='https://github.com/KarrLab/wc_utils',

    author='Arthur Goldberg',
    author_email='Arthur.Goldberg@mssm.edu',

    license='MIT',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 3 - Alpha',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Whole-cell Models',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: MIT License',

        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],

    keywords='whole-cell modeling',

    # packages not prepared yet
    packages=find_packages(exclude=['tests', 'tests.*']),
    package_data={
        'wc_utils': [
            'debug_logs/config.default.cfg',
            'debug_logs/config.schema.cfg',
        ],
    },

    install_requires=install_requires,
    tests_require=tests_require,
    dependency_links=dependency_links,
)
