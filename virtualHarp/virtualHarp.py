#!/usr/bin/env python2.7

import Voxel
import numpy as np
import cv2
import scipy.misc
from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph as pg

# Assumes ubuntu. Tried on Ubuntu 16.04
#Packages needed -
# Voxel SDK - Follow the instructions in the github documentation - https://github.com/3dtof/voxelsdk/wiki/Installation-on-Linux
# Python open CV - apt-get install python-opencv
# Midi synthesis - 	easy_install mingus
#					apt-get install fluidsynth

from mingus.midi import fluidsynth
fluidsynth.init('/usr/share/sounds/sf2/FluidR3_GM.sf2',"alsa") 

sys = Voxel.CameraSystem()

devices = sys.scan()
print devices

print "Got ", len(devices), " devices"

CONTOUR_SIZE_THRESHOLD=10 #minimum size of the blob that is processed.
MAX_DEPTH=0.7 #max distance from the camera
MIN_DEPTH=0.2 #min distance from the camera
MAX_VELOCITY=127
MIN_VELOCITY=32
MAX_WIDTH=0.4 #max horizontal movement allowed
MAX_NOTES=16 #number of notes represented in the above width

app = QtGui.QApplication([])
imv = pg.ImageView()
imv.show()

#Since we are emulating only the pure notes, we need to map the note numbers to the actual key number.
#0:C, 2:D, 4:E, 5:F, 7:G, 9:A, 11:B
lut={0:0,1:2,2:4,3:5,4:7,5:9,6:11}

fluidsynth.set_instrument(0,46) #Choosing Harp
fluidsynth.set_instrument(1,99) #Choosing Atmosphere


prevNoteMap={}
curNoteMap={}


def convertPosToNote(pos):
	'''convert the X position (horizontal position) to a note'''
	digitalPos=MAX_NOTES*(MAX_WIDTH/2-pos)/MAX_WIDTH #2 octaves of only the pure notes. no sharps or flats.
	if(digitalPos<0):
		note=-1
	elif(digitalPos>MAX_NOTES):
		note=-1
	elif((digitalPos-np.round(digitalPos))<0.2):
		note=-1
	else:
		digitalPos=int(np.round(digitalPos))
		octave=digitalPos/7
		digitalPos=digitalPos%7
		note=36+octave*12+lut[digitalPos] #starting from C4
	return note

def playNote(note,velocity):
	'''Play a specified note with the set velocity'''
	if(note>=0):
		if(velocity<MIN_VELOCITY):
			velocity=MIN_VELOCITY
		fluidsynth.play_Note(note,0,velocity)
		fluidsynth.play_Note(note,1,velocity//2)
		print note

def stopNote(note):
	'''Stop a specified note'''
	if(note>=0):
		fluidsynth.stop_Note(note,0)
		fluidsynth.stop_Note(note,1)
			

def playNotes():
	'''Plays all the notes in curNoteMap'''
	global curNoteMap,prevNoteMap
	for note,velocity in curNoteMap.iteritems():
		if(prevNoteMap.has_key(note)):
			if(prevNoteMap[note]!=velocity):
				playNote(note,velocity)
			del prevNoteMap[note]
		else:
			playNote(note,velocity)
	for note,velocity in prevNoteMap.iteritems():
		stopNote(note)
	prevNoteMap=curNoteMap
	curNoteMap={}
	
def callback(depthCamera, frame, type):
	global curNoteMap
	try:
		pointCloudFrame = Voxel.XYZIPointCloudFrame.typeCast(frame)
		pcf = np.nan_to_num(np.array(pointCloudFrame, copy = True))
		#print pcf.dtype,pcf.shape
		xFrame=(pcf[:,0]).reshape(240,320)
		yFrame=(pcf[:,1]).reshape(240,320) #not doing anything with this.
		zFrame=(pcf[:,2]).reshape(240,320)
		iFrame=(pcf[:,3]).reshape(240,320)
		iFrame=iFrame*4096
		mask=iFrame>10
		zFrame=zFrame*mask #amplitude thresholding
		iFrame=iFrame*mask
		zFrame=zFrame*(zFrame>MIN_DEPTH)*(zFrame<MAX_DEPTH) #filter by distances
		
		zImage=(zFrame*255).astype("uint8")#scipy.misc.toimage(zFrame)
		
		imv.setImage((np.transpose(iFrame))[::-1,:]) #video display
		ret,zThresh=cv2.threshold(zImage,int(0.1*255),255,cv2.THRESH_BINARY)
		contours, hierarchy = cv2.findContours(zThresh,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE )
		
		for contour in contours:
			#print "Found contour"
			contourSize = cv2.contourArea(contour)
			if contourSize > CONTOUR_SIZE_THRESHOLD:
				maskImage=np.zeros(zThresh.shape)
				cv2.drawContours(maskImage,[contour,],-1,1,-1)
				depth=np.sum(maskImage*zFrame*iFrame)/np.sum(iFrame*maskImage) #calculate average depth of each blob
				velocity=MAX_VELOCITY*(MAX_DEPTH-depth)/(MAX_DEPTH-MIN_DEPTH) #map the depth to velocity (velocity in music refers to the intensity of the key stroke
				
				position=np.sum(maskImage*xFrame*iFrame)/np.sum(iFrame*maskImage)
				curNoteMap[convertPosToNote(position)]=int(velocity)
		playNotes()
		
	except Exception as e:
		print str(e)
		exit(0)


if len(devices) > 0:
	gdepthCamera = sys.connect(devices[0])

	frameSize = Voxel.FrameSize()
	frameSize.height = 240
	frameSize.width = 320 #using OPT8241-CDK-EVM
	gdepthCamera.setFrameSize(frameSize)
	gdepthCamera.setCameraProfile(3) #short range profile. A better way to do this is to list the profiles loaded in the camera and match the name

	gdepthCamera.registerCallback(Voxel.DepthCamera.FRAME_XYZI_POINT_CLOUD_FRAME, callback)
	gdepthCamera.start()

app.exec_() #start the qt loop