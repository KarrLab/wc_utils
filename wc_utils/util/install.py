""" Installation utilities.

:Author: Jonathan Karr <karr@mssm.edu>
:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2016-10-22
:Copyright: 2016, Karr Lab
:License: MIT
"""

import pip
import re


def parse_requirements(req_file_lines):
    ''' Parse requirements.txt file.

    Return lists of package dependencies and dependency links, to be used
    as `install_requires`/`tests_require` and `dependency_links`
    by `setuptools.setup`.

    Args:
        req_file_lines (:obj:`str`): lines in the requirements.txt file

    Returns:
        :obj:`tuple`: list of dependencies, list of dependency links
    '''
    # todo: support the rest of the requirements.txt format
    # see: https://pip.pypa.io/en/stable/reference/pip_install/#requirements-file-format

    install_requires = []
    dependency_links = []
    for line in req_file_lines:
        # strip comment
        i_egg = line.find('#egg')
        i_comment = line.find('#', i_egg + 1)
        if i_comment >= 0:
            line = line[0:i_comment]

        # strip white space
        pkg_src = line.rstrip()

        # parse out package name, version constraints, and package location
        match = re.match('^(.+#egg=)([a-z0-9_\-]+)(.*)$', pkg_src, re.IGNORECASE)
        if match:
            pkg_id = match.group(2) + match.group(3)
            dependency_links.append(match.group(1) + match.group(2))
        else:
            pkg_id = pkg_src
        install_requires.append(pkg_id)

        install_requires = list(set(install_requires))
        dependency_links = list(set(dependency_links))

    return (install_requires, dependency_links)


def install_dependencies(dependency_links):
    for dependency_link in dependency_links:
        pip.main(['install', dependency_link])
