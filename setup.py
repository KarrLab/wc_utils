"""A setuptools based setup module, template copied from https://github.com/pypa/sampleproject

See also:
https://packaging.python.org/en/latest/distributing.html
"""

from setuptools import setup, find_packages
from codecs import open
from os import path
import pip
import re
import wc_utils
from wc_utils.util.installation import install_packages

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# parse requirements.txt
install_requires = []
with open('requirements.txt', 'r') as f:
    for line in f.readlines():
        pkg_src = line.rstrip()
        match = re.match('^.+#egg=(.*?)$', pkg_src)
        if match:
            pkg_id = match.group(1)
            pip.main(['install', pkg_src])
        else:
            pkg_id = pkg_src
        install_requires.append(pkg_id)

x = install_packages( open('requirements.txt').readline() )
print( x, install_requires )
assert x == install_requires

setup(
    name='wc_utils',
    version=wc_utils.__version__,

    description='Utilities for whole-cell modeling',
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

    install_requires=install_requires,
)