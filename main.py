import os
import numpy as np
import cv2
from PIL import Image
import shutil
import math
import time 
from queue import Queue
import threading


def crop(image):
    '''Slice Image into single vertical pixel'''
    height, width, channels = image.shape
    slice = width // 2
    cropped = image[0:height, slice:slice + 1]
    return cropped

def concatArrSliver(filenameArr, resizeFactor):
    arrSliver = np.concatenate([np.array(Image.open(x).resize((resizeFactor, height))) for x in filenameArr], axis=1)
    return arrSliver

def splitArr(a, n):
    k, m = divmod(len(a), n)
    return list((a[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in range(n)))

def processSplit(filenameArr, resizeFactor, numofsplits=4):
    arrofSlivers = splitArr(filenameArr, numofsplits)
    sliverDict = {}
    que = Queue()
    threads = []
    for i in range(numofsplits):
        #threads.append(threading.Thread(target = lambda q, arg1, arg2: q.put(concatArrSliver(arg1, arg2)), args=(que, arrofSlivers[i], resizeFactor))) 
        threads.append(threading.Thread(target = lambda m, arg1, arg2: m.update({i : concatArrSliver(arg1, arg2)}), args=(sliverDict, arrofSlivers[i], resizeFactor)))
        threads[-1].start()
    for t in threads:
        t.join()
    return sliverDict

def getResizeFactor(frameCount):
        if (frameCount < 1920):
            return math.ceil(1920/frameCount)
        else: 
            return 1

#Create directory to store pixel slices 
if os.path.exists('tempdir') == False:
    os.mkdir('tempdir')

#Open video file
vid = cv2.VideoCapture('./videos/fish.mp4')

#Get video properties
frameCount = int(vid.get(cv2.CAP_PROP_FRAME_COUNT))
width  = int(vid.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(vid.get(cv2.CAP_PROP_FRAME_HEIGHT))

print(frameCount, width,  height)

#Determine how much to stretch image
#resizeFactor = getResizeFactor(frameCount)
resizeFactor = 2

#Create variables for for loop
count = 0
filenameArr = []
success, image  = vid.read()

#Test - try setting a frame to specific index in video
#vid.set(cv2.CAP_PROP_POS_FRAMES, 4000)

#Iterate through each frame, crop and save 
loopTimeStart = time.time()
while success:
    croppedImage = crop(image)
    cv2.imwrite("./tempdir/frame%06d.jpg" % count, croppedImage)
    filenameArr.append("frame%06d.jpg" % count)
    success,image = vid.read()
    count += 1

loopTimeStop = time.time() 

#Change directory into tempdir to gain access to the files
os.chdir('tempdir')

#Combine arrays
sliverDict = processSplit(filenameArr, resizeFactor)
concatenated = Image.fromarray(np.concatenate([sliverDict[key] for key in sorted(sliverDict.keys())], axis=1))

#Change back to save file 
os.chdir('..')

#Remove the tempdir that contains the files 
shutil.rmtree('C:\\Users\\jan99375\\Documents\\PythonProjects\\ImageAlterting\\tempdir')

#Save the file
concatenated.save("render - work.jpg")