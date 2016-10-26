"""A setuptools based setup module, template copied from https://github.com/pypa/sampleproject

See also:
https://packaging.python.org/en/latest/distributing.html
"""

from setuptools import setup, find_packages
from codecs import open
from os import path
from wc_utils.util.installation import parse_requirements, install_dependencies_from_links
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

# install non-PyPI dependencies
install_dependencies_from_links(dependency_links)

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
