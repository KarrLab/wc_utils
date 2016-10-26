""" Installation utilities.

:Author: Jonathan Karr <karr@mssm.edu>
:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2016-10-22
:Copyright: 2016, Karr Lab
:License: MIT
"""

import pip, re

def install_packages( req_file_lines ):
    ''' Install packages specified in requirements.txt.
    
    Use pip to install a package's requirements. Also return
    a list of package dependencies, to be used as install_requires
    by setup() in setup.py.

    Args:
        req_file_lines (:obj:`str`): lines in the requirements.txt file

    Returns:
        :obj:`list`: list of dependencies parsed from `req_file_lines`
    '''
    install_requires=[]
    for line in req_file_lines:
        pkg_src = line.rstrip()
        # todo: support the rest of the requirements.txt format
        # see: https://pip.pypa.io/en/stable/reference/pip_install/#requirements-file-format
        match = re.match('^.+#egg=(.*?)$', pkg_src)
        if match:
            pkg_id = match.group(1)
            pip.main(['install', '-U', pkg_src])
        else:
            pkg_id = pkg_src
        install_requires.append(pkg_id)
    return install_requires
