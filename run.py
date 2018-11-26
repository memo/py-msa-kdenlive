#!/usr/bin/env python2
# -*- coding: utf-8 -*-
'''
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
'''

from __future__ import absolute_import, division, print_function

if __name__=='__main__':
    
    import numpy as np
    import sys
    import argparse
    from pprint import pprint

    import msa.kdenlive

    parser = argparse.ArgumentParser()
    parser.add_argument('-k', '--kdenlive_prj_path', required=True, help='path to kdenlive project')
    parser.add_argument('-n', '--track_name', default='Video 1', help='name of track in kdenlive project to use')
    parser.add_argument('-i', '--input_path', required=True, help='path to input numpy array (e.g. containing z-sequence) or video file')
    parser.add_argument('-g', '--groundtruth_path', default='', help='[OPTIONAL] path to ground truth edited array or video file (for checking functionality')
    parser.add_argument('-o', '--output_path', default='out.npy', help='path to desired output numpy array containing conformed sequence')
    parser.add_argument('-v', '--verbose', default=0, type=int, help='if 1, dumps entire edit to console (comparing to ground truth if available')
    args = parser.parse_args()
    
    pprint(args.__dict__)
    
    # load project
    print('Loading Kdenlive project:', args.kdenlive_prj_path)
    prj = msa.kdenlive.Project(args.kdenlive_prj_path)
    
    # get all tracks
    track_names = msa.kdenlive.get_track_names(prj.tracks)
    print('Found {} tracks, called {}'.format(len(track_names), track_names))
    
    # find the track(s) with the right name. Note this returns a list
    try:
        track = msa.kdenlive.find_tracks_by_name(prj.tracks, args.track_name)[0]
        print('Track "{}" found with length {} frames'.format(args.track_name, track[msa.kdenlive.KEY_LENGTH]))
    except:
        print('Track "{}" not found'.format(args.track_name))
        sys.exit(1)
        
        
    
    def load(path):
        try:
            if path.endswith('.npy'): # Load numpy array
                print('Loading numpy array', path)
                return np.load(path)
            
            if path.endswith('.mp4') or path.endswith('.mov'): # Load video
                print('Loading video', path)
                import skvideo.io # pip install sk-video.
                return skvideo.io.vread(path)
    
            
        except:
            print('Could not load', path)
            sys.exit(1)
            
            
    # load input
    src = load(args.input_path)
    
    # load ground truth already edited sequence if it exists (for checking)
    ref = load(args.groundtruth_path) if args.groundtruth_path else None
          
        
    # conform (apply edit)
    print('Conforming edit on track "{}" with {} frames onto {}'.format(track[msa.kdenlive.KEY_TRACK_NAME], track[msa.kdenlive.KEY_LENGTH], args.input_path))
    edited = msa.kdenlive.conform_track_edit(track, src, empty_value=0)
    
    if args.verbose:
        for i,v in enumerate(edited): 
            print('-'*80)
            print('frame #{}'.format(i))
            # if we have ground truth, display ground truth first, and then edited
            if ref is not None: print('ref: ', ref[i]) 
            print('edit:', edited[i])
    
    
    print('='*80)
    print('Saving conformed sequence to', args.output_path)
    np.save(args.output_path, edited)
    
    
    if ref is not None:
        print('Mean squared error between ground truth edit and python edit is', np.linalg.norm(ref - edited))
        
                