""" File utils

:Author: Jonathan Karr <karr@mssm.edu>
:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2018-05-11
:Copyright: 2018, Karr Lab
:License: MIT
"""

import os
import shutil
import errno


def copytree_to_existing_destination(src, dst):
    """ Copy files from :obj:`src` to :obj:`dst`, overwriting existing files with the same paths
    and keeping all other existing directories and files

    Args:
        src (:obj:`str`): path to source
        dst (:obj:`str`): path to destination
    """
    if os.path.isdir(src):
        if not os.path.isdir(dst):
            os.mkdir(dst)
            
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
    else:
        shutil.copy2(src, dst)


def normalize_filename(filename, dir=None):
    """ Normalize a filename to its fully expanded, real, absolute path

    Expand `filename` by interpreting a user’s home directory, environment variables, and
    normalizing its path. If `filename` is not an absolute path and `dir` is provided then
    return a full path of `filename` in `dir`.

    Args:
        filename (:obj:`str`): a filename
        dir (:obj:`str`, optional): a directory that contains `filename`

    Returns:
        :obj:`str`: `filename`'s fully expanded, absolute path

    Raises:
        :obj:`ValueError`: if neither `filename` after expansion nor `dir` are absolute
    """
    filename = os.path.expanduser(filename)
    filename = os.path.expandvars(filename)
    if os.path.isabs(filename):
        return os.path.normpath(filename)
    elif dir:
        # raise exception if dir isn't absolute
        if not os.path.isabs(dir):
            raise ValueError("directory '{}' isn't absolute".format(dir))
        return os.path.normpath(os.path.join(dir, filename))
    else:
        return os.path.abspath(filename)


def normalize_filenames(filenames, absolute_file=None):
    """ Normalize filenames relative to directory containing existing file

    Args:
        filenames (:obj:`list` of :obj:`str`): list of filenames
        absolute_file (:obj:`str`, optional): file whose directory contains files in `filenames`

    Returns:
        :obj:`list` of :obj:`str`: absolute paths for files in `filenames`
    """
    dir = None
    if absolute_file:
        dir = os.path.dirname(absolute_file)
    return [normalize_filename(filename, dir=dir) for filename in filenames]


def remove_silently(filename):
    """ Delete file `filename` if it exist, but report no error if it doesn't

    Args:
        filename (:obj:`str`): a filename

    Raises:
        :obj:`Exception`: if an error occurs that is not 'no such file or directory'
    """
    try:
        os.remove(filename)
    except OSError as e:
        # errno.ENOENT: no such file or directory
        if e.errno != errno.ENOENT:
            # re-raise exception if a different error occurred
            raise   # pragma: no cover; unclear how to execute this line
