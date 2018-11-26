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

import numpy as np
import os
import json
import codecs
import random
from tqdm import tqdm

import msa.fileio

import msa.logger
logger = msa.logger.getLogger(__name__)

def has(o, k, relaxed=True):
    '''checks if k is in o, and if it is, checks if not None (or evaluates to True)'''
    if not hasattr(o,k): return False
    if relaxed: return getattr(o,k)
    return getattr(o,k) is not None

def dict_key(d, key):
    '''return reference to a key of a dict, creating it (as a dict) if nessecary'''
    if key not in d: d[key] = {}
    return d[key]

def find_by_key_in_dict(d, target):
    '''return dict filtered by keys containing target'''
    return {key:value for key,value in d.items() if target in key}


def find_by_keys_in_dict(d, targets):
    '''return dict filtered by keys containing targets (list)'''
    return {key:value for key,value in d.items() if any(substring in key for substring in targets)}


def find_by_key_in_dict_list(l, target, key='name', exact=True):
    '''search list l and return dicts with key containing or matching (if exact)
    Example:
        l = [ dict(name='name', value='memo'), dict(name='age', value=43), dict(name='height', value=175)]
        d = find_by_key_in_dict_list(l, 'age', key='name')

    '''
    if exact: return filter(lambda x: key in x and target==x[key], l)
    else: return filter(lambda x: key in x and target in x[key], l)


def find_by_attr_in_obj_list(l, target, key='name', exact=True):
    '''search list l and return dicts or objects with key or attr containing or matching target (if exact)'''
#    if exact: return filter(lambda x: hasattr(x, key) and target==getattr(x, key), l)
#    else: return filter(lambda x: key in x and target in getattr(x, key), l)
    if exact: return [x for x in l if hasattr(x, key) and target == getattr(x, key)]
    else: return [x for x in l if hasattr(x, key) and target in getattr(x, key)]
    
    
def find_by_key(o, target, key='name', exact=True):
    '''convenient method (for backwards compatibility)'''
    if type(o)==dict: return find_by_key_in_dict(o, target)
    elif type(o)==list: return find_by_key_in_dict_list(o, target, key, exact)

    
def find_by_attr(l, target, key='name', exact=True):
    '''convenient method (for backwards compatibility)'''
    find_by_attr_in_obj_list(l, target, key='name', exact=True)

   

def list_to_dict_by_key(l, name_key='name', value_key='value', d={}):
    '''create a single dict extracting name,value pairs from list of dicts
    e.g. given a list of 'property' dicts where each dict is {name=property_name, value=property_value}
    optionally pass in d if want to use OrderedDict or update an existing dict
    
    Example:
        l = [ dict(name='name', value='memo'), dict(name='age', value=43), dict(name='height', value=175)]
        d = list_to_dict_by_key(l)
    '''
    for x in l:
        if name_key in x:
            if value_key in x:
                d[x[name_key]] = x[value_key]
            else:
                logger.warning("name_key '{}' found but no value '{}' in {}".format(name_key, value_key, x))
    return d

    
def get_members(obj):
    '''returns public variable names of a class or object (i.e. not private or functions)'''
    return [n for n in dir(obj) if not callable(getattr(obj, n)) and not n.startswith("__")]


def get_members_and_info(obj):
    '''returns public variable (name, type, value) of a class or object (i.e. not private or functions)'''
    return [(n, type(getattr(obj, n)), getattr(obj, n)) for n in dir(obj) if not callable(getattr(obj, n)) and not n.startswith("__")]


def array_to_str(a, in_range, ch_range=(33,122)): # map to range !-z
    '''convert array a (in range arange) to a hex string'''
    a = np.uint8(np.interp(a.flatten(), in_range, ch_range))
    a = [chr(x) for x in a]
    s = ''.join(a)
    return s


# def copy_params_to_obj(src, dst):
#     '''copy params from (object) src to (object) dst (not recursive)'''
#     for p in get_members(src):
#         setattr(dst, p, getattr(src, p))

def interpolate_dict(src_a, src_b, dst, t, bool_switch_t=0.1):
    '''interpolate params from (dict) src_a to (dict) src_b
    and copy to (pyqtgraph parameter group) dst (not recursive)'''
    for k in src_b:
        a = src_a[k]
        b = src_b[k]
        if type(b) == bool:
            dst[k] = b if t > bool_switch_t else a
        else:
            dst[k] = type(b)((b-a) * t + a)

# def interpolate_params(src_a, src_b, dst, t, bool_switch_t=0.1):
#     '''interpolate params from (dict) src_a to (dict) src_b
#     and copy to (pyqtgraph parameter group) dst (not recursive)'''
#     for p in get_members(src_b):
#         pa = getattr(src_a, p)
#         pb = getattr(src_b, p)
#         if type(pb) == bool:
#             setattr(dst, p, pb if t > bool_switch_t else pa)
#         else:
#             setattr(dst, p, type(pb)((pb-pa) * t + pa))

# for testing merge_dicts_by_name
#D={'i':'Hello', 'j':'World', 'modules':[{'name':'a', 'val':1}, {'name':'b', 'val':2}, {'name':'c', 'val':3}, {'name':'d', 'val':4}] }
#P={'i':'Goodbye', 'modules':[{'name':'a', 'val':10}, {'name':'c', 'val':30}] }

def merge_dicts_by_name(P, D, id_key='name', root='', depth=0, indent='   '):
    '''
    merge from dict (or list of dicts) P into D.
    i.e. can think of D as Default settings, and P as a subset containing user Preferences.
    Any value in P or D can be a dict or a list of dicts
    in which case same behaviour will apply (through recursion):
        lists are iterated and dicts are matched between P and D
        dicts are matched via an id_key (only at same hierarchy depth / level)
        matching dicts are updated with same behaviour
        for anything else P overwrites D

    P : dict or list of dicts (e.g. containing user Preferences, subset of D)
    D : dict or list of dicts (e.g. Default settings)
    id_key : the key by which sub-dicts are compared against (e.g. 'name')
    root : for keeping track of full path during recursion
    depth : keep track of recursion depth (for indenting)
    indent : with what to indent (if verbose)
    '''

    indent_full = indent * depth
    logger.info('{}{} P:{} D:{}'.format(indent_full, root, type(P), type(D)))

    if type(P)==list: # D and P are lists of dicts
        assert(type(D)==type(P))
        for p_i, p_dict in enumerate(P): # iterate dicts in P
            path = root + '[' + str(p_i) + ']'
            logger.info('{}list item: {}'.format(indent_full, path))
            d_id = p_dict[id_key] # get name of current dict
            # find corresponding dict in D
            d_dict = D[ next(i for (i,d) in enumerate(D) if d[id_key] == d_id) ]
            merge_dicts_by_name(p_dict, d_dict, id_key=id_key, root=path, depth=depth+1, indent=indent)

    elif type(P)==dict:
        assert(type(D)==type(P))
        for k in P:
            path = root + '.' + k
            print('{}key: {}'.format(indent_full, path), end=' : ')
            if k in D:
                if type(P[k]) in [dict, list]:
                    print()
                    merge_dicts_by_name(P[k], D[k], id_key=id_key, root=path, depth=depth+1, indent=indent)
                else:
                    print(D[k], 'overwritten by', P[k])
                    D[k] = P[k]

            else:
                print(indent_full, 'Warning: Key {} in P not found in D'.format(path))

    else:
        print(indent_full, "Warning: Don't know what to do with these types", type(P), type(D))


def save_json(o, path, indent=4, sort_keys=True, ensure_ascii=False):
    '''save object as json, only works with serialiseable objects'''
    
    def default(obj):
        '''https://stackoverflow.com/questions/15876180/convert-numpy-arrays-in-a-nested-dictionary-into-list-whilst-preserving-dictiona?rq=1'''
        if isinstance(obj, np.ndarray):
            return obj.tolist()
#        raise TypeError('Not serializable')
        return '{} not serializable'.format(type(obj))
    
    if not path.endswith('.json'): path = path + '.json'
    path = msa.fileio.expand(path)
    logger.debug(path)
    msa.fileio.create_dir_for_file(path)
    with open(path, 'w') as f:
        json.dump(o, f, indent=indent, sort_keys=sort_keys, ensure_ascii=ensure_ascii, default=default)


def load_json(path):
    '''load object from json'''
    if not path.endswith('.json'): path = path + '.json'
    path = msa.fileio.expand(path)
    logger.debug(path)
    return json.load(open(path, 'r'))


#
#def pickle_json(o, path, indent=4):
#    '''pickle object as json'''
#    jsonpickle.set_preferred_backend('json')
#    jsonpickle.set_encoder_options('json', sort_keys=False, indent=indent)
#    j = jsonpickle.encode(o)
#    with open(path, 'w') as f:
#        f.write(j)
#
#
#def unpickle_json(path):
#    '''unpickle object from json'''
#    with open(path, 'r') as f:
#        o = jsonpickle.decode(f)
#        return o



def load_txt_files(folder, limit_chars=-1, ext='.txt', encoding='utf-8'):
    """load text files in folder, return dict {key: filename, value: text}"""
    logger.info(folder)
    # get src text filenames
    in_filenames = os.listdir(folder)
    if ext != None and len(ext) > 0:
        in_filenames = [x for x in in_filenames if x.endswith(ext)]

    # load and collect texts
    texts = dict()
    for fn in in_filenames:
        with codecs.open(os.path.join(folder, fn), encoding=encoding) as f:
            txt = f.read()
            if limit_chars > 0: txt = txt[:limit_chars]
            texts[fn] = txt
            logger.info('Loaded {} chars from {}'.format(len(txt), fn))
    return texts



def create_seqs(texts, seq_len, seq_step):
    """expects a dict of texts, if it isn't a dict, it will make it a list"""
    if type(texts) != dict: texts = {'text':texts}

    text = '\n'.join(texts.values())
    if type(text) != unicode: text = unicode(text, 'utf-8')
    # hack, encode to ascii for now
    # text = text.encode('ascii','ignore')
#    chars = list(set(text)).sort()  # IF THIS CHANGES WITH NEW CORPUS, PRE_TRAINED MODELS SCREWUP
#    print('Corpus length: ', len(text), '. Total chars:', len(chars))
#    char_maps = {
#        'len': len(chars),
#        'char_indices' : dict((c, i) for i, c in enumerate(chars)),
#        'indices_char' : dict((i, c) for i, c in enumerate(chars))
#    }

    # cut the text in semi-redundant sequences of seq_len characters
    # TODO: should separate the separate corpuses
    x_seqs = []
    y_chars = []
    for i in range(0, len(text) - seq_len, seq_step):
        x_seqs.append(text[i: i + seq_len])
        y_chars.append(text[i + seq_len])

    logger.info('Number of sequences : {}'.format(len(x_seqs)))

    return x_seqs, y_chars


def rand_seq(text, seq_len, start_max=-1):
    start_max = len(text) if start_max < 0 else start_max
    start_index = random.randint(0, start_max - seq_len - 1)
    s = text[start_index: start_index + seq_len]
    return s



def iterate_in_batches(X, batch_size, show_progress=False, progress_desc=''):
#    g = (itertools.islice(X, i, i+size) for i in xrange(0, len(X), size))
    g = (X[i:i+batch_size] for i in range(0, len(X), batch_size))
    if show_progress: g = tqdm(g, desc=progress_desc, total=len(X)//batch_size)
    return g