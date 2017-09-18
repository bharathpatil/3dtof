'''
Created on 19-Jul-2017

@author: bharath
'''
#!/usr/bin/env python2.7

import Voxel
import numpy as np
import datetime
import logging as log
import os

sys = Voxel.CameraSystem()

devices = sys.scan()
print devices

print "Got ", len(devices), " devices"

path=os.getenv("HOME")+"/"
fileName="dump.npy"

prevNoteMap={}
curNoteMap={}

WIDTH=80
HEIGHT=60

startTime=None
fullArr=[]

def callback(depthCamera, frame, type):
	global curNoteMap
	try:
		pointCloudFrame = Voxel.XYZIPointCloudFrame.typeCast(frame)
		pcf = np.nan_to_num(np.array(pointCloudFrame, copy = True))
		
		#print pcf.dtype,pcf.shape
		xFrame=(pcf[:,0]).reshape(HEIGHT,WIDTH)
		yFrame=(pcf[:,1]).reshape(HEIGHT,WIDTH) #not doing anything with this.
		zFrame=(pcf[:,2]).reshape(HEIGHT,WIDTH)
		iFrame=(pcf[:,3]).reshape(HEIGHT,WIDTH)
		iFrame=iFrame*4096
#		mask=iFrame>10
#		zFrame=zFrame*mask #amplitude thresholding
#		iFrame=iFrame*mask
#		zFrame=zFrame*(zFrame>MIN_DEPTH)*(zFrame<MAX_DEPTH) #filter by distances
		
		zImage=(zFrame*255).astype("uint8")#scipy.misc.toimage(zFrame)
		currentTime=datetime.datetime.now()
		fullArr.append(pcf)
		if((currentTime-startTime).seconds>30):
			np.save(path+fileName,np.array(fullArr))
			print "Done taking data"
			exit(0)
		
	except Exception as e:
		print str(e)
		exit(0)


if len(devices) > 0:
	log.basicConfig(level=log.DEBUG)
	gdepthCamera = sys.connect(devices[0])

	frameSize = Voxel.FrameSize()
	frameSize.height = HEIGHT
	frameSize.width = WIDTH #using OPT8241-CDK-EVM
	gdepthCamera.setFrameSize(frameSize)
#	 gdepthCamera.setCameraProfile(3) #short range profile. A better way to do this is to list the profiles loaded in the camera and match the name

	gdepthCamera.registerCallback(Voxel.DepthCamera.FRAME_XYZI_POINT_CLOUD_FRAME, callback)
	name="Normal"
	names=gdepthCamera.getCameraProfileNames()
	for i in names.keys():
		print names[i]
		if(names[i]==name):
			break
	print "Using profile number : %d (%s)"%(i,name)
	
	startTime=datetime.datetime.now()
	gdepthCamera.setb("disable_temp_corr",True)
	gdepthCamera.seti("coeff_sensor",0)
	gdepthCamera.seti("coeff_illum",0)
	gdepthCamera.setu("sub_frame_cnt_max1",8)
	gdepthCamera.setb("shutter_en",True)
	
	#print "Sub frames:",gdepthCamera.getu("sub_frame_cnt_max1")
	#print "Shutter:"+str((gdepthCamera.getb("shutter_en")))
	gdepthCamera.start()

	while(1):
		pass