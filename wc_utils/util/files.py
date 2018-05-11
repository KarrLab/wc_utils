""" File utils

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2018-05-11
:Copyright: 2018, Karr Lab
:License: MIT
"""

import os
import shutil


def copytree_to_existing_destination(src, dst):
    """ Copy files from :obj:`src` to :obj:`dst`, overwriting existing files with the same paths
    and keeping all other existing directories and files

    Args:
        src (:obj:`str`): path to source
        dst (:obj:`str`): path to destination
    """
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            if os.path.isdir(d):
                shutil.copystat(s, d)
                copytree_to_existing_destination(s, d)
            else:
                shutil.copytree(s, d)
        else:
            shutil.copy2(s, d)
