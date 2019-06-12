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
    arrSliver = np.concatenate(
        [np.array(Image.open(x).resize((resizeFactor, 1080))) for x in filenameArr], axis=1)
    # GET HEIGHT OF IMAGE SOMEHOW
    return arrSliver


def splitArr(a, n):
    '''Splits an array into n nearly equal parts'''
    k, m = divmod(len(a), n)
    return list((a[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in range(n)))


def retrieveConcatenatedImage(filenameArr, resizeFactor, numofsplits=2):
    '''Splits filenamearr into n arrays, concatenates n arrays using n threads, returns final images'''

    os.chdir('tempdir')
    arrofSlivers = splitArr(filenameArr, numofsplits)
    sliverDict = {}
    threads = []

    for i in range(numofsplits):
        threads.append(threading.Thread(target=lambda m, arg1, arg2: m.update(
            {i: concatArrSliver(arg1, arg2)}), args=(sliverDict, arrofSlivers[i], resizeFactor)))
        threads[-1].start()

    for t in threads:
        t.join()

    os.chdir('..')

    return Image.fromarray(np.concatenate([sliverDict[key] for key in sorted(sliverDict.keys())], axis=1))


def createFrames(videoName, numofsplits=2):
    '''Reads video using n threads and returns list of filenames'''
    filenameSliverList = []
    threads = []
    vidList = {}

    # Create numofsplits instances of vid
    for x in range(numofsplits):
        vidList[x] = cv2.VideoCapture('./videos/%s' % videoName)

    frameCount = int(vidList[0].get(cv2.CAP_PROP_FRAME_COUNT))
    if frameCount > 65500:
        frameCount = 65500

    print(frameCount)

    # Keep track of where each thread should read
    frameDivisions = math.floor(frameCount / numofsplits)
    threadFrameStart = 0
    threadFrameEnd = frameDivisions

    for i in range(numofsplits):
        if i == numofsplits:
            # Last thread should read until end. Rounding issues
            threadFrameEnd = frameCount

        threads.append(threading.Thread(target=lambda l, arg1, arg2, arg3: l.append(frameCreator(
            arg1, arg2, arg3)), args=(filenameSliverList, vidList[i], threadFrameStart, threadFrameEnd)))
        threads[-1].start()
        threadFrameStart += frameDivisions
        threadFrameEnd += frameDivisions

    for t in threads:
        t.join()

    for x in range(numofsplits):
        vidList[x].release()

    filenameSliverList = [item for sublist in filenameSliverList for item in sublist]
    return sorted(filenameSliverList)


def getResizeFactor(frameCount):
    '''Determines how much cells should be stretched... might remove this'''
    if (frameCount < 1920):
        return math.ceil(1920/frameCount)
    else:
        return 1


def frameCreator(vid, start, end):
    '''Sets vid frame to the start index and creates frames until the end'''
    # Set the vid frame to the start frame index
    vid.set(cv2.CAP_PROP_POS_FRAMES, start)

    # Create variables for for loop
    count = 0
    filenameSliver = []
    success, image = vid.read()

    while success and vid.get(cv2.CAP_PROP_POS_FRAMES) < end:
        croppedImage = crop(image)
        cv2.imwrite("./tempdir/frame%010d.jpg" % vid.get(cv2.CAP_PROP_POS_FRAMES), croppedImage)
        filenameSliver.append("frame%010d.jpg" % vid.get(cv2.CAP_PROP_POS_FRAMES))
        success, image = vid.read()
        count += 1

    return filenameSliver


# Create directory to store pixel slices
if os.path.exists('Images') == False:
    os.mkdir('Images')

while True:
    # Create directory to store pixel slices
    if os.path.exists('tempdir') == False:
        os.mkdir('tempdir')

    filename = input("Enter name of file (including extension): ")
    fileWithoutExt = os.path.splitext(filename)[0]

    if (filename == "q" or filename == ""):
        exit()
        
    elif (os.path.isfile("./videos/%s" % filename)):
        try: 
            startTimeNew = time.time()
            print("Reading file...")
            filenameArr = createFrames(filename)
            stopTimeNew = time.time()

            # Retrieve final image and save it
            finalImage = retrieveConcatenatedImage(filenameArr, 2)

            #finalImage.save("workrender - %s.jpg" % file)
            finalImage.save("./Images/homerender - %s.jpg" % fileWithoutExt)
            # Remove the tempdir that contains the files
            shutil.rmtree('tempdir')
            img = cv2.imread("./Images/homerender - %s.jpg" % fileWithoutExt)
            cv2.imshow('image', img)
            cv2.waitKey(0)
            cv2.destroyAllWindows()

            print(stopTimeNew - startTimeNew)

        except:
            print("Error creating file. Try again")

    else:
        print("File does not exist.")

'''
#Open video file
file = 'wavesrock'
filename = file + '.mp4'

startTimeNew = time.time()
filenameArr = createFrames(filename)
stopTimeNew = time.time()

# Retrieve final image and save it
finalImage = retrieveConcatenatedImage(filenameArr, 2)
#finalImage.save("workrender - %s.jpg" % file)
finalImage.save("./Images/homerender - %s.jpg" % file)
'''
