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

Usage:
    import msa.logger
    logger = msa.logger.getLogger(__name__)
    
    logger.info(msg)
    logger.warning(msg)
    logger.error(msg)
    etc.

"""
from __future__ import absolute_import, division, print_function
from builtins import range # pip install future


import logging
logging.basicConfig(level=logging.INFO, 
#                    datefmt='%m/%d/%Y %H:%M:%S',
                    format= 
#                    '%(levelname)s | %(asctime)s | %(name)s.%(funcName)s() [L%(lineno)d] : %(message)s')
                    '[%(levelname)s] %(asctime)s %(name)s.%(funcName)s() : %(message)s')

def getLogger(name):
    return logging.getLogger(name)

logger = getLogger(__name__)

def test_levels():
    logger.debug('details')
    logger.info('something')
    logger.warning('uh oh')
    logger.error('crap')
    logger.critical('zzzz')
    
def test_fn_args(a=1, b=2, c=3, *args, **kwargs):
    logger.info(locals())