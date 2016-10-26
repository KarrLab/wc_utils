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
    install_requires = []
    dependency_links = []
    for line in req_file_lines:
        pkg_src = line.rstrip()
        # todo: support the rest of the requirements.txt format
        # see: https://pip.pypa.io/en/stable/reference/pip_install/#requirements-file-format
        match = re.match('^.+#egg=(.*?)$', pkg_src)
        if match:
            pkg_id = match.group(1)
            dependency_links.append(pkg_src)
        else:
            pkg_id = pkg_src
        install_requires.append(pkg_id)
    return (install_requires, dependency_links)


def install_dependencies_from_links(dependency_links):
    for dependency_link in dependency_links:
        pip.main(['install', dependency_link])
