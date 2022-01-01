# -*- coding: utf-8 -*-
"""
Take a video file and randomly shuffle segments from it.

Created on Tue Feb  9 20:39:11 2021

@author: CodeWanderer
"""
import moviepy.editor
import random

#Parameter
filepath = '10s count.avi'

#Sequence of starting and ending frame times (in seconds)
startstop = [(0,1),
            (1,2),
            (2,4),
            (6,7),
            (8,9),
            (9,10)]

#Shuffle and append
startstop_s = startstop[:-1] #all except last section
random.shuffle(startstop_s) #shuffles array randomly
startstop_s.append(startstop[-1]) #append last section to end

#Generate movie file
clip = moviepy.editor.VideoFileClip(filepath) #Load video from filepath into Python
output=[clip.subclip(*ss) for ss in startstop_s] #Make new video clip object with shuffled order
moviepy.editor.concatenate_videoclips(output).write_videofile(filepath.split('.')[0] + '_shuffle.mp4',preset='ultrafast') #Save video clip to file
clip.close() #close resource