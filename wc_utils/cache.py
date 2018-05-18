""" Caching

:Author: Jonathan Karr <jonrkarr@gmail.com>
:Date: 2018-03-30
:Copyright: 2018, Karr Lab
:License: MIT
"""

import diskcache
import functools
import glob
import hashlib
import inspect
import os
import types


class Cache(diskcache.FanoutCache):
    """ Cache that shards keys (including the file content of keys that represent file names) and values 

    Attributes:
        hash_block_size (:obj:`int`): block size to use for hashing the content of file arguments
    """

    DEFAULT_DIRECTORY = os.path.expanduser('~/.wc/cache/')

    def __init__(self, directory=DEFAULT_DIRECTORY, hash_block_size=65536, **kwargs):
        """
        Args:
            directory (:obj:`str`, optional): cache directory
            kwargs (:obj:`dict`, optional): arguments to :obj:`diskcache.FanoutCache`
        """
        super(Cache, self).__init__(directory, **kwargs)
        self.hash_block_size = hash_block_size

    def memoize(self, name=None, typed=False, expire=None, tag=None, filename_args=None, filename_kwargs=None):
        """ Memoizing cache decorator

        Args:
            name (:obj:`str`, optional): name given for callable
            typed (:obj:`bool`, optional): cache different types separately
            expire (:obj:`float`, optional): seconds until arguments expire
            tag (:obj:`str`, optional): text to associate with arguments
            filename_args (:obj:`list`, optional): list of indices of arguments that represent filenames
            filename_kwargs (:obj:`list`, optional): list of keys of keyword arguments that represent filenames

        Returns:
            :obj:`types.FunctionType`: callable decorator
        """
        if callable(name):
            raise TypeError('name cannot be callable')

        filename_args = filename_args or []
        filename_kwargs = filename_kwargs or []

        def decorator(function):
            """ Decorator created by memoize call for callable. """
            if name is None:
                try:
                    # Python 3
                    reference = function.__qualname__
                except AttributeError:  # pragma: no cover
                    # Python 2
                    reference = function.__name__  # pragma: no cover

                reference = function.__module__ + reference
            else:
                reference = name

            reference = (reference,)

            @functools.wraps(function)
            def wrapper(*args, **kwargs):
                "Wrapper for callable to cache arguments and return values."

                # match arguments to function signature
                func_signature = inspect.signature(function)
                proc_args = []
                proc_kwargs = {}
                for i_param, (name, param) in enumerate(func_signature.parameters.items()):
                    if param.kind is not inspect.Parameter.POSITIONAL_OR_KEYWORD:
                        raise NotImplementedError('Memoize decorator only supports positional-or-keyword arguments. '
                                                  'Submit issue to request support for optional arguments')

                    if param.default is inspect._empty:
                        if i_param < len(args):
                            val = args[i_param]
                        elif param.name in kwargs:
                            val = kwargs[param.name]
                        else:
                            raise TypeError("{} missing required positional argument '{}'".format(function.__name__, param.name))
                        proc_args.append(val)
                    else:
                        if i_param < len(args):
                            val = args[i_param]
                        elif param.name in kwargs:
                            val = kwargs[param.name]
                        else:
                            val = param.default
                        proc_kwargs[param.name] = val

                # generate key from arguments
                key = reference + tuple(proc_args)

                if proc_kwargs:
                    key += (diskcache.core.ENOVAL,)
                    sorted_items = sorted(proc_kwargs.items())

                    for item in sorted_items:
                        key += item

                if typed:
                    key += tuple(type(arg) for arg in proc_args)

                    if proc_kwargs:
                        key += tuple(type(value) for _, value in sorted_items)

                for filename_arg in filename_args:
                    stats = []
                    for filename in glob.glob(proc_args[filename_arg]):
                        stats.append((os.path.getmtime(filename), self._hash_file_content(filename)))
                    key += tuple(stats)

                for filename_kwarg in filename_kwargs:
                    if filename_kwarg in proc_kwargs:
                        stats = []
                        for filename in glob.glob(proc_kwargs[filename_kwarg]):
                            stats.append((os.path.getmtime(filename), self._hash_file_content(filename)))
                        key += tuple(stats)

                result = self.get(key, default=diskcache.core.ENOVAL, retry=True)

                if result is diskcache.core.ENOVAL:
                    result = function(*args, **kwargs)
                    self.set(key, result, expire=expire, tag=tag, retry=True)

                return result

            return wrapper

        return decorator

    def _hash_file_content(self, path):
        """ Hash the content of a file

        Args:
            path (:obj:`str`): path to the file to hash the contents of

        Returns:
            :obj:`str`: hash of the content of the file
        """
        hasher = hashlib.sha1()
        with open(path, 'rb') as file:
            buffer = file.read(self.hash_block_size)
            while len(buffer) > 0:
                hasher.update(buffer)
                buffer = file.read(self.hash_block_size)
        return hasher.hexdigest()


cache = Cache()
# :obj:`Cache`: cache

memoize = cache.memoize
# :obj:`types.FunctionType`: memoize method
