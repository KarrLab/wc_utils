""" Installation utilities.

:Author: Jonathan Karr <karr@mssm.edu>
:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2016-10-22
:Copyright: 2016, Karr Lab
:License: MIT
"""

import pip, re

def install_packages( req_file ):
    ''' Install packages specified in requirements.txt.
    
    Use pip to install a package's requirements listed in `req_file`. Also return
    a list of package dependencies, to be used as install_requires
    by setup() in setup.py.

    Args:
        :req_file:`str`: name of requirements file

    Returns:
        :obj:`list`: list of dependencies parsed from `req_file`
    '''
    install_requires=[]
    for line in open():
        pkg_src = line.rstrip()
        # todo: support the rest of the requirements.txt format
        # see: https://pip.pypa.io/en/stable/reference/pip_install/#requirements-file-format
        match = re.match('^.+#egg=(.*?)$', pkg_src)
        if match:
            pkg_id = match.group(1)
            pip.main(['install', pkg_src])
        else:
            pkg_id = pkg_src
        install_requires.append(pkg_id)
    return install_requires
