import os
import numpy as np
import cv2
from PIL import Image
import shutil
import math
import time
import threading


def crop(image):
    '''Slice Image into single vertical pixel'''
    height, width, channels = image.shape
    slice = width // 2
    cropped = image[0:height, slice:slice + 1]
    return cropped

def concatArrSliver(filenameArr, resizeFactor):
    '''Concatenates array sliver that is passed into it and stretches depending on resizefactor'''
    arrSliver = np.concatenate([np.array(Image.open(x).resize((resizeFactor, height))) for x in filenameArr], axis=1)
    return arrSliver

def splitArr(a, n):
    '''Splits an array into n nearly equal parts'''
    k, m = divmod(len(a), n)
    return list((a[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in range(n)))

def retrieveConcatenatedImage(filenameArr, resizeFactor, numofsplits=4):
    '''Splits filenamearr into n arrays, concatenates n arrays using n threads, returns final images'''

    os.chdir('tempdir')
    arrofSlivers = splitArr(filenameArr, numofsplits)
    sliverDict = {}
    threads = []

    for i in range(numofsplits):
        threads.append(threading.Thread(target = lambda m, arg1, arg2: m.update({i : concatArrSliver(arg1, arg2)}), args=(sliverDict, arrofSlivers[i], resizeFactor)))
        threads[-1].start()

    for t in threads:
        t.join()

    os.chdir('..')

    return Image.fromarray(np.concatenate([sliverDict[key] for key in sorted(sliverDict.keys())], axis=1))

def getResizeFactor(frameCount):
    '''Determines how much cells should be stretched... might remove this'''
    if (frameCount < 1920):
        return math.ceil(1920/frameCount)
    else: 
        return 1

def frameCreator(vid, start, end):
    '''Sets vid frame to the start index and creates frames until the end'''

    #Set the vid frame to the start frame index
    vid.set(cv2.CAP_PROP_POS_FRAMES, start)

    #Create variables for for loop
    count = 0
    filenameSliver = []
    success, image  = vid.read()
    
    while success and vid.get(cv2.CAP_PROP_POS_FRAMES) < end:
        croppedImage = crop(image)
        cv2.imwrite("./tempdir/frame%010d.jpg" % vid.get(cv2.CAP_PROP_POS_FRAMES), croppedImage)
        filenameSliver.append("frame%010d.jpg" % vid.get(cv2.CAP_PROP_POS_FRAMES))
        success,image = vid.read()
        count += 1

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

#Iterate through each frame, crop and save 
while success:
    croppedImage = crop(image)
    cv2.imwrite("./tempdir/frame%010d.jpg" % vid.get(cv2.CAP_PROP_POS_FRAMES), croppedImage)
    filenameArr.append("frame%010d.jpg" % vid.get(cv2.CAP_PROP_POS_FRAMES))
    success,image = vid.read()
    count += 1

#Retrieve final image and save it 
finalImage = retrieveConcatenatedImage(filenameArr, 2)
finalImage.save("render - work.jpg")

#Remove the tempdir that contains the files 
shutil.rmtree('C:\\Users\\jan99375\\Documents\\PythonProjects\\ImageAlterting\\tempdir')