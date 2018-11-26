#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Copyright 2018, Memo Akten, www.memo.tv

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

from __future__ import absolute_import, division, print_function
from builtins import range # pip install future

import os

import msa.logger
logger = msa.logger.getLogger(__name__)
    
def expand(path):
    return os.path.expanduser(os.path.expandvars(path))


def join(*paths):
    '''like os.path.join, but expands each path first, in case it's absolute'''
    paths = [expand(p) for p in paths]
    return os.path.join(*paths)


def filename(path):
    '''returns just filename without extension from full path'''
    return os.path.splitext(os.path.split(path)[-1])[0]

def datapath(path, config, key='data_root'):
    '''assumes config has a 'data_root' key, and path is relative to that'''
    return join(config[key], path)


def create_dir(folder_path):
    """create a directory if it doesn't exist. silently fail if it already does exist"""
    if folder_path and not os.path.exists(folder_path): os.makedirs(folder_path)


def create_dir_for_file(file_path):
    """create a directory if for a target file. silently fail if it already does exist"""
    create_dir(os.path.split(file_path)[0])
    

def get_paths(path, extensions=['jpg', 'jpeg', 'png', ''], ignore_ext=[], sort=True, raise_errors=False, followlinks=True):
    '''returns a (flat) list of paths of all files of (certain types) recursively under a path
    path can be a folder, a textfile with a filename per line (relative to the file), or a list or tuple
    '''    
    logger.info('{}, ext:{}, ignore:{}, sort{}, follow_links:{}'.format(path, extensions, ignore_ext, sort, followlinks))
    
    # return list as is if it's a list or tuple
    if type(path) in (list, tuple): return path

    # check path exists
    path = os.path.expanduser(os.path.expandvars(path))
    if not os.path.exists(path):
        s = "Path '{}' not found".format(path)
        logger.info(s)
        if raise_errors: raise IOError(s)
        else: return

    if os.path.isfile(path):
        if path.endswith('txt'): # if text file, open
            with open(path, 'r') as f: txt = f.read().splitlines()
            paths = [os.path.join(os.path.split(path)[0], x) for x in txt]
        else:
            return [path]
    else:
        if type(extensions)==str: extensions = extensions.split(' ')
        if type(ignore_ext)==str: ignore_ext = ignore_ext.split(' ')
        try:
            paths = [unicode(os.path.join(root, name), 'utf-8') # python 2
                     for root, dirs, files in os.walk(path, followlinks=followlinks)
                     for name in files
                     if name.lower().endswith(tuple(extensions)) and not name.lower().endswith(tuple(ignore_ext))]
        except:
            paths = [str(os.path.join(root, name)) # python 3
                     for root, dirs, files in os.walk(path)
                     for name in files
                     if name.lower().endswith(tuple(extensions)) and not name.lower().endswith(tuple(ignore_ext))]

    if sort: paths = sorted(paths)

    if len(paths) == 0:
        s = "No files {} found in {}".format(extensions, path)
        logger.warning(s)
        if raise_errors: raise IOError(s)
        
    return paths


def test_tar(path):
    '''TODO: allow get paths and msa.imgseq to operate on tars'''
    import tarfile
    import zipfile
    
    #https://docs.python.org/2/library/tarfile.html
    if tarfile.is_tarfile(path): t = tarfile.open(path, mode='r')
    
    #https://docs.python.org/2/library/zipfile.html
    if zipfile.is_zipfile(path): z = zipfile.ZipFile(path, mode='r')
