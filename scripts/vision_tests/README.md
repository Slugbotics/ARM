# Computer vision Test Scripts
## This directory is a series of computer vision tests

### To run any of these scripts, make sure you have installed all the packages in the root directoy's requirments.txt file and the local requirment.txt
## use "python -m pip install -r requirments.txt" or "python3 -m pip install -r requirments.txt"
## to exit a script, hold ctrl and press C (ctrl-C)

## DistanceByObject.py
### Will use YOLOv3 to identify objects, then will compare the size of identified objects against pre-selected sizes to estimate distance.

## blob_detector.py
### This script will collect areas that are visually simmilar and then draw a circle around them
### changing the params in this file will greatly effect the type of blobs collected.

## rave.py
### This script will segment the image into regions

## edge_detector.py
### this script will identify all the edges in an image, this could be a foundation to identifying different types of objects.

## camera_ports_list.py
### This script will check what camera ports are avalable on a computer, you need to make sure at least one camera shows up in 'working ports'.

## ATest1000.py
### Will load a camera and display the video feed, this is just a test script.