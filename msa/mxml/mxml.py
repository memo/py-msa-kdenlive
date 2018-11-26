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

from lxml import etree
from collections import OrderedDict

import msa.utils

# save tag, children and value under these keys
default_special_keys = dict(tag='TAG', children='CHILDREN', value='VALUE')

def e_to_dict(xml_element, add_empty=False, special_keys=default_special_keys):
    '''convert an xml element to dictionary
    preserves order of all tags, even if mixed up etc (unlike most examples online)
    explodes attributes into root of dict (potentially dangerous, if there is an attribute with same name as special keys)
    '''
    tag_key, children_key, value_key = special_keys['tag'], special_keys['children'], special_keys['value']
    if type(xml_element) != etree._Element: return xml_element
    assert(msa.utils.find_key(xml_element.attrib, special_keys.values()) is None) # make sure keys aren't in attrib
    d = { tag_key:xml_element.tag }
    if add_empty or len(xml_element) > 0: d[children_key] = [e_to_dict(c) for c in xml_element]
    if add_empty or xml_element.text: d[value_key] = xml_element.text
    d.update(**xml_element.attrib)
    return d

def children_by_key(xml_element, tag, keys=['id', 'name'], **kwargs):
    '''find all children with denoted tag, and create ordered dict
    where attribute denoted by 'key' is used as key
    if 'key' is list or tuple, search attributes in order of list
    '''
    return OrderedDict([(x.attrib[msa.utils.find_key(x.attrib, keys)], e_to_dict(x, **kwargs)) for x in xml_element.findall(tag)])

