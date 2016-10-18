"""A setuptools based setup module, template copied from https://github.com/pypa/sampleproject

See also:
https://packaging.python.org/en/latest/distributing.html
"""

from setuptools import setup, find_packages
from codecs import open
from os import path

import wc_utilities

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='wc_utilities',
    version=wc_utilities.__version__,

    description='Utilities for whole-cell modeling components',
    long_description=long_description,

    # The project's main homepage.
    url='https://github.com/KarrLab',

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

    install_requires='configobj PyYAML numpy six enum34'.split() ,
)