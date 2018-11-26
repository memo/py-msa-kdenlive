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

import time
import datetime
import socket
import os
import inspect
import threading

verbose=1

def get_fn(stack=1):
    return inspect.stack()[stack] # stack==1, to return caller's info 

def get_fn_name(stack=1):
    return inspect.stack()[stack][3] # stack==1, to return caller's info 

def log_fn(fn, *args, **kwargs):
    '''call function and dump to log'''
    y = fn(*args, **kwargs)
    if verbose:
        s = []
        if hasattr(fn, 'func_name'): s += [fn.func_name]
        s += [str(y)]
        s = ' | '.join(s)
        if verbose == 1: print(s)
        elif verbose == 2: print(s, args, kwargs)
    return y

def extract_kwargs(prefix, kwargs):
    ''' searches for keys in a dict starting with prefix, and returns a new dict with only those, with prefix removed
    useful for managing **kwargs in nested functions
    '''
    return { key.replace(prefix, ''):kwargs[key] for key in kwargs if key.startswith(prefix)}
    

def doublestarmap(fn, kwargs_list):
    '''run function fn for each kwargs in kwargs_list'''
    return [fn(**kwargs) for kwargs in kwargs_list]


def doublestarmap_in_thread(fn, kwargs_list):
    '''run function fn for each kwargs in kwargs_list in separate thread
    Example:
    -------
        def foo(a,b): print(a,b)
        kwargs_list = [dict(a=1,b=2), dict(a=10,b=20), dict(a=100,b=200)] 
        run_in_thread(foo, kwargs_list)
    '''
    thread = threading.Thread(target=doublestarmap, kwargs=dict(fn=fn, kwargs_list=kwargs_list))
    thread.start()
    return thread


def timestamp(s='%Y%m%d.%H%M%S', ts=None):
    if not ts: ts = time.time()
    st = datetime.datetime.fromtimestamp(ts).strftime(s)
    return st


def find_key(haystack, needles):
    '''given a list of needles, return first needle in haystack'''
    for k in needles:
        if k in haystack: return k
        
        
def hostname():
    return socket.gethostname()


def mstr(a):
    if type(a) in [list, tuple]:
        return '({})'.format(','.join([str(i) for i in a]))
    return str(a)


def check_attr(args, attr):
    return hasattr(args, attr) and getattr(args, attr) is not None and getattr(args, attr) 

def have_display():
    '''from https://stackoverflow.com/questions/8257385/automatic-detection-of-display-availability-with-matplotlib'''
    b = "DISPLAY" in os.environ
    if not b and os.name != 'posix': # code below is slow, so only do it on windows where the above doesn't always work
        exitval = os.system('python -c "import matplotlib.pyplot as plt; plt.figure()"')
        b = (exitval == 0)
    return b

def matplotlib_backend():
    '''Need this to switch to correct backend for headless.'''
    import matplotlib
    if not have_display(): matplotlib.use('Agg')
    
