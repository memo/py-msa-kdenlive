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


More info on motivations etc at
https://medium.com/@memoakten/deep-meditations-meaningful-exploration-of-ones-inner-self-576aab2f3894

Load and parse kdenlive xml project format
https://kdenlive.org/en/project/kdenlive-project-file-format/

GOAL:
    1. Either generate random z values and save npy, or load npy into model. Render out video of z values
        1a. npy file containing sequence of z values
        1b. video file which is output of those z values from a DNN
    2. Edit video in kdenlive
    3. Load EDL (not real EDL, kdenlive project) in python, conform with (apply edit to) z-npy
    4. Feed conformed z-npy back into model for render
    
Currently supports very simple edits: cuts, joins, trims etc.
No speed changes, no transitions, no effects
Only tested with one track (should work with more).

"""

from __future__ import absolute_import, division, print_function
from builtins import range # pip install future


from lxml import etree
from collections import OrderedDict
import os
import numpy as np

import msa.mxml
import msa.data

import msa.logger
logger = msa.logger.getLogger(__name__)

KEY_NAME = 'name'
KEY_TRACK_NAME = 'kdenlive:track_name'
KEY_PRODUCER = 'producer'
KEY_PLAYLIST = 'playlist'
KEY_LENGTH = 'length'
KEY_CHILDREN = 'children'
KEY_IN = 'in'
KEY_OUT = 'out'
KEY_START = 'start'


class Project:
    def __init__(self, xml_path):
        self.tree = etree.parse(os.path.expanduser(os.path.expandvars(xml_path)))
        self.root = self.tree.getroot()
        
        # list of producers (i.e. media)
        self.producers = msa.mxml.children_by_key(self.root, KEY_PRODUCER, add_empty=False)
        
        # playlists include tracks, and also media bin etc
        self.playlists = msa.mxml.children_by_key(self.root, KEY_PLAYLIST, add_empty=False)
        
        # get track playlists, and update start, duration info etc.
        # tracks are in reverse order (bottom to top)
        self.tracks = OrderedDict([(k,v) for k,v in self.playlists.items() if k.startswith(KEY_PLAYLIST)])
        map(update_track_properties, self.tracks.values())
        map(update_track_info, self.tracks.values())
        
        
        
def update_track_properties(track_dict, special_keys=msa.mxml.default_special_keys):
    '''extract track property children into root of dict'''
    return msa.data.list_to_dict_by_key(track_dict[special_keys[KEY_CHILDREN]], name_key=KEY_NAME, value_key=special_keys['value'], d=track_dict)
        

def update_track_info(track_dict, special_keys=msa.mxml.default_special_keys):
    '''
    Given a track_dict, update start times
    example track_dict:
        producer '3' is the media
        first clip content contains frames 5-29 (timeline: 0-24)
        25 frames of blank (timeline: 25-49)
        clip contents frames 20-89 (timeline: )
{'CHILDREN': [
    {'TAG': 'property', 'VALUE': 'Video 1', 'name': 'kdenlive:track_name'},
    {'TAG': 'property', 'VALUE': '0', 'name': 'kdenlive:locked_track'},
    {'TAG': 'entry',  'in': '10', 'out': '29', 'producer': '1_video'},
    {'TAG': 'blank', 'length': '10'},
    {'TAG': 'entry', 'in': '35', 'out': '44', 'producer': '1_video'},
    {'TAG': 'blank', 'length': '5'},
    {'TAG': 'entry', 'in': '60', 'out': '60', 'producer': '1_video'}
    ],
'TAG': 'playlist',
'VALUE': '\n  ',
'id': 'playlist3'})])
    
After this function, becomes:
{'CHILDREN': [
    {'TAG': 'property', 'VALUE': 'Video 1', 'name': 'kdenlive:track_name'},
    {'TAG': 'property', 'VALUE': '0', 'name': 'kdenlive:locked_track'},
    {'TAG': 'entry', 'in': 10, 'length': 20, 'out': 29, 'producer': '1_video', 'start': 0},
    {'TAG': 'blank', 'length': 10, 'start': 20},
    {'TAG': 'entry', 'in': 35, 'length': 10, 'out': 44, 'producer': '1_video', 'start': 30},
    {'TAG': 'blank', 'length': 5, 'start': 40},
    {'TAG': 'entry', 'in': 60, 'length': 1, 'out': 60, 'producer': '1_video', 'start': 45}],
'TAG': 'playlist',
'id': 'playlist3',
'length': 46})])
    '''
    children_key = special_keys[KEY_CHILDREN]
    start = 0
    for c in track_dict[children_key]:
#        print(c)
        length = None
        if all([x in c for x in [KEY_OUT, KEY_IN]]): 
            c[KEY_IN], c[KEY_OUT] = int(c[KEY_IN]), int(c[KEY_OUT])
            length = c[KEY_OUT] - c[KEY_IN] + 1
        elif KEY_LENGTH in c: length = int(c[KEY_LENGTH])
#        else: raise KeyError("No KEY_IN, KEY_OUT, or KEY_LENGTH. What is this!?")
        if length:
            c.update(length=length, start=start)
            start += length
    track_dict[KEY_LENGTH] = start

            
def conform_track_edit(track_dict, source, special_keys=msa.mxml.default_special_keys, empty_value=0):
    '''
    given a track_dict, apply edit to indexable source (time is on the 0th axis)
    return ndarray edited
    if source is a dict treat it as {producer : indexable}, otherwise use it as is
    fill the empty parts of target with empty_value
    '''
    if len(source) == 0: return None
    
    #create empty return ndarray of correct length and shape
    target = np.zeros((track_dict[KEY_LENGTH], ) + source.shape[1:], dtype=source.dtype)
    if empty_value: target.fill(empty_value)
    children_key = special_keys[KEY_CHILDREN]
    for c in track_dict[children_key]:
        if all([x in c for x in [KEY_OUT, KEY_IN, KEY_LENGTH, KEY_START]]):  
            i,s,l = c[KEY_IN], c[KEY_START], c[KEY_LENGTH]
            logger.debug('Applying edit in:{} length:{} to start:{}', i, l, s)
            src = source[c[KEY_PRODUCER]] if type(source)==dict else source
            target[s:s+l] = src[i:i+l]
    
    return target


def get_track_names(tracks):
    return [t[KEY_TRACK_NAME] for _,t in tracks.iteritems()]

            
def find_tracks_by_name(tracks, name, exact=True):
    return msa.data.find_by_key_in_dict_list(tracks.values(), target=name, key=KEY_TRACK_NAME, exact=exact)
 

'''
Example kdenlive file:

<?xml version='1.0' encoding='utf-8'?>
<mlt title="Anonymous Submission" version="6.5.0" root="/home/memo/Documents" producer="main bin" LC_NUMERIC="en_GB.UTF-8">
 <profile width="1920" frame_rate_den="1" height="1080" display_aspect_num="16" display_aspect_den="9" frame_rate_num="30" colorspace="709" sample_aspect_den="1" description="HD 1080p 30 fps" progressive="1" sample_aspect_num="1"/>
 <producer id="3" title="Anonymous Submission" out="149" in="0">
  <property name="length">150</property>
  <property name="eof">pause</property>
  <property name="resource">#ffff0000</property>
  <property name="aspect_ratio">1</property>
  <property name="mlt_service">color</property>
  <property name="kdenlive:clipname">Color Clip</property>
  <property name="kdenlive:folderid">-1</property>
  <property name="kdenlive:duration">150</property>
  <property name="kdenlive:file_hash">9196813120dc5c505072516b15baf414</property>
  <property name="global_feed">1</property>
 </producer>
 <playlist id="main bin">
  <property name="kdenlive:docproperties.audiotargettrack">-1</property>
  <property name="kdenlive:docproperties.decimalPoint">.</property>
  <property name="kdenlive:docproperties.dirtypreviewchunks"/>
  <property name="kdenlive:docproperties.disablepreview">0</property>
  <property name="kdenlive:docproperties.documentid">1532636710526</property>
  <property name="kdenlive:docproperties.enableproxy">0</property>
  <property name="kdenlive:docproperties.generateimageproxy">0</property>
  <property name="kdenlive:docproperties.generateproxy">0</property>
  <property name="kdenlive:docproperties.kdenliveversion">17.04.3</property>
  <property name="kdenlive:docproperties.position">109</property>
  <property name="kdenlive:docproperties.previewchunks"/>
  <property name="kdenlive:docproperties.previewextension"/>
  <property name="kdenlive:docproperties.previewparameters"/>
  <property name="kdenlive:docproperties.profile">atsc_1080p_30</property>
  <property name="kdenlive:docproperties.proxyextension">mpg</property>
  <property name="kdenlive:docproperties.proxyimageminsize">2000</property>
  <property name="kdenlive:docproperties.proxyminsize">1000</property>
  <property name="kdenlive:docproperties.proxyparams">-vf scale=640:-1 -g 5 -qscale 6 -ab 128k -vcodec mpeg2video -acodec mp2</property>
  <property name="kdenlive:docproperties.version">0.95</property>
  <property name="kdenlive:docproperties.verticalzoom">1</property>
  <property name="kdenlive:docproperties.videotargettrack">1</property>
  <property name="kdenlive:docproperties.zonein">0</property>
  <property name="kdenlive:docproperties.zoneout">100</property>
  <property name="kdenlive:docproperties.zoom">3</property>
  <property name="kdenlive:documentnotes"/>
  <property name="kdenlive:clipgroups"/>
  <property name="xml_retain">1</property>
  <entry out="149" producer="3" in="0"/>
 </playlist>
 <producer id="black" out="54000" in="0">
  <property name="length">54001</property>
  <property name="eof">pause</property>
  <property name="resource">black</property>
  <property name="aspect_ratio">0</property>
  <property name="mlt_service">colour</property>
  <property name="set.test_audio">0</property>
 </producer>
 <playlist id="black_track">
  <entry out="116" producer="black" in="0"/>
 </playlist>
 <playlist id="playlist3">
  <property name="kdenlive:track_name">My Video Track</property>
  <entry out="29" producer="3" in="5"/>
  <blank length="15"/>
  <entry out="89" producer="3" in="20"/>
  <blank length="5"/>
  <entry out="30" producer="3" in="30"/>
 </playlist>
 <tractor id="maintractor" title="Anonymous Submission" global_feed="1" out="116" in="0">
  <track producer="black_track"/>
  <track producer="playlist3"/>
  <transition id="transition0">
   <property name="a_track">0</property>
   <property name="b_track">1</property>
   <property name="mlt_service">mix</property>
   <property name="always_active">1</property>
   <property name="combine">1</property>
   <property name="internal_added">237</property>
  </transition>
  <transition id="transition1" out="89" in="20">
   <property name="a_track">0</property>
   <property name="b_track">1</property>
   <property name="start">0/0:100%x100%</property>
   <property name="factory">loader</property>
   <property name="aligned">1</property>
   <property name="progressive">1</property>
   <property name="mlt_service">composite</property>
   <property name="always_active">1</property>
   <property name="valign">middle</property>
   <property name="halign">centre</property>
   <property name="fill">1</property>
   <property name="geometry">0=0/0:1920x1080</property>
   <property name="internal_added">237</property>
  </transition>
 </tractor>
</mlt>
'''    