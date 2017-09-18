'''
Created on 05-Aug-2017

@author: bharath
'''
'''
Created on 19-Jul-2017

@author: bharath
'''
#!/usr/bin/env python2.7

import numpy as np
from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph as pg
from pyqtgraph.dockarea import *
import time


app = QtGui.QApplication([])

win = QtGui.QMainWindow()
win.setWindowTitle("Recorded Data")
area = DockArea()
win.setCentralWidget(area)
win.resize(1500,800)
w1 = pg.LayoutWidget()
imv1 = pg.ImageView()
imv1.setPredefinedGradient('spectrum')
imv2 = pg.ImageView()
plot1 = pg.PlotWidget()
plot2 = pg.PlotWidget()
curve1 = plot1.plot(pen='r')
curve2 = plot2.plot(pen='g')
d1 = Dock("Depth image", size=(500,400))
d2 = Dock("Intensity image", size=(500,400))
d3 = Dock("Depth Average", size=(500,400))
d4 = Dock("Intensity Average", size=(500,400))
area.addDock(d1,'left')
area.addDock(d2,'right')
area.addDock(d3,'bottom')
area.addDock(d4,'right',d3)
d1.addWidget(imv1)
d2.addWidget(imv2)
d3.addWidget(plot1)
d4.addWidget(plot2)
win.show()

prevNoteMap={}
curNoteMap={}

#path="/home/bharath/nini/tech/software/resources/breathrateExpts/"
path=os.getenv("HOME")+"/"
fileName="dump.npy"

WIDTH=80
HEIGHT=60

startTime=None
fullArr=[]

FRAME_TIME=1/60.0

if __name__=="__main__":
	fullArr=np.load(path+fileName)
	print fullArr.shape
	curve1Data=np.zeros(int(5*(1/FRAME_TIME))) #5 seconds of data
	curve2Data=np.zeros(int(5*(1/FRAME_TIME))) #5 seconds of data
	for pcf in fullArr:
		#print pcf.dtype,pcf.shape
		xFrame=(pcf[:,0]).reshape(HEIGHT,WIDTH)
		yFrame=(pcf[:,1]).reshape(HEIGHT,WIDTH) #not doing anything with this.
		zFrame=(pcf[:,2]).reshape(HEIGHT,WIDTH)
		iFrame=(pcf[:,3]).reshape(HEIGHT,WIDTH)
		iFrame=iFrame*4096
		mask=iFrame>50
		zFrame=zFrame*mask #amplitude thresholding
#		iFrame=iFrame*mask
#		zFrame=zFrame*(zFrame>MIN_DEPTH)*(zFrame<MAX_DEPTH) #filter by distances
		zImage=(zFrame*255).astype("uint8")#scipy.misc.toimage(zFrame)
		imv1.setImage((np.transpose(zFrame))[::-1,:])
		imv2.setImage((np.transpose(iFrame))[::-1,:]) #video display
		curve1Data[0]=np.average(zFrame[35:45,25:35],weights=iFrame[35:45,25:35])
		curve1Data=np.roll(curve1Data,-1)
		curve1.setData(curve1Data)
		curve2Data[0]=np.average(iFrame[35:45,25:35])
		curve2Data=np.roll(curve2Data,-1)
		curve2.setData(curve2Data)
#		imv.setImage((np.transpose(iFrame))[::-1,:]) #video display
		app.processEvents()
		time.sleep(FRAME_TIME)
