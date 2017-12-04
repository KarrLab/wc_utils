"""A setuptools based setup module

See also:
https://packaging.python.org/en/latest/distributing.html
"""

import setuptools
try:
    import pkg_utils
except ImportError:
    import pip
    pip.main(['install', 'git+https://github.com/KarrLab/pkg_utils.git#egg=pkg_utils'])
    import pkg_utils
import os

name = 'wc_utils'
dirname = os.path.dirname(__file__)

# get package metadata
md = pkg_utils.get_package_metadata(dirname, name)

# set needed pygit2 version
import re
libgit2_path = os.getenv("LIBGIT2")
if not libgit2_path:
    if os.name == 'nt':
        libgit2_path = os.path.join(os.getenv("ProgramFiles"), 'libgit2')
    else:
        libgit2_path = '/usr/local'
version_filename = os.path.join(libgit2_path, 'include', 'git2', 'version.h')

libgit2_version = None
if os.path.isfile(version_filename):
    with open(version_filename, 'r') as file:
        for line in file:
            match = re.findall('define *LIBGIT2_VERSION *"(.*?)"', line.strip())
            if match:
                libgit2_version = match[0]
                break

if libgit2_version:
    md.extras_require['git'] = 'pygit2 == {}'.format(libgit2_version)
else:
    warnings.warn(('wc_utils requires libgit2. Please install libgit2 and then retry installing '
                   'wc_utils. Please see https://libgit2.github.com for installation instructions.'))

# install package
setuptools.setup(
    name=name,
    version=md.version,

    description='Utilities for whole-cell modeling',
    long_description=md.long_description,

    # The project's main homepage.
    url='https://github.com/KarrLab/' + name,
    download_url='https://github.com/KarrLab/' + name,

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
    packages=setuptools.find_packages(exclude=['tests', 'tests.*']),
    package_data={
        name: [
            'VERSION',
            'debug_logs/config.default.cfg',
            'debug_logs/config.schema.cfg',
            'util/units.txt',            
        ],
    },

    install_requires=md.install_requires,
    extras_require=md.extras_require,
    tests_require=md.tests_require,
    dependency_links=md.dependency_links,
)
