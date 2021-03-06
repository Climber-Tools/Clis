import cv2
import numpy as np
import shutil
import sys
import os
import argparse
import pyexiv2
import tempfile
from subprocess import Popen, PIPE
from glob import glob

sys.path.append("..")

os.chdir(os.path.dirname(os.path.abspath(__file__)))

from config import *
from utilities import *


def get_convex_hull_mask(image):
    """Get the mask using the convex hull of green pixels. Currently unused (but kept as a pet)."""
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    lower_green = np.array([65,60,60])
    upper_green = np.array([80,255,255])

    mask = cv2.inRange(hsv, lower_green, upper_green)

    kernel = np.ones((5,5),'int')
    dilated = cv2.dilate(mask,kernel)

    res = cv2.bitwise_and(image,image, mask=mask)

    ret, thresh = cv2.threshold(cv2.cvtColor(res,cv2.COLOR_BGR2GRAY),3,255,cv2.THRESH_BINARY)
    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

    # create hull array for convex hull points
    hull = []
    for contour in contours:
        hull += list(contour)

    hull = cv2.convexHull(np.array(hull), False)
    hull = np.array([[h[0] for h in hull]])

    # create an empty black image
    drawing = np.zeros(image.shape[:2], np.uint8)

    cv2.fillPoly(drawing, hull, (255, 255, 255))

    return drawing


def get_contour_mask(image):
    """Get the image by using contours from the pixel threshold."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    ret, thresh = cv2.threshold(gray, MASKING_THRESHOLD, 255, cv2.THRESH_BINARY)

    # detect the contours on the binary image using cv2.CHAIN_APPROX_NONE
    contours, hierarchy = cv2.findContours(image=thresh, mode=cv2.RETR_TREE, method=cv2.CHAIN_APPROX_NONE)

    # find the biggest countour (c) by the area
    c = max(contours, key = cv2.contourArea)

    # create an empty black image
    drawing = np.zeros(image.shape[:2], np.uint8)
    cv2.fillPoly(drawing, np.array(c), (255, 255, 255))

    # flood fill from origin on black pixels
    cv2.floodFill(drawing, None,
            seedPoint=(image.shape[1] // 2, image.shape[0] // 2),
            newVal=(255, 255, 255),
            loDiff=(1, 1, 1, 1), upDiff=(1, 1, 1, 1))

    # smoothen a bit
    kernel2 = np.ones((5, 5), np.float32)/25
    img = cv2.filter2D(src=drawing, ddepth=-1, kernel=kernel2)

    return drawing


printer = Printer("mask")

parser = argparse.ArgumentParser()
parser.add_argument("folders", nargs='+', help="The folders to process the images of")

arguments = parser.parse_args()

for folder in arguments.folders:
    printer.full(f"masking images from '{folder}':")
    for name in sorted(glob(os.path.join(folder, "_*.jpg"))):
        printer.begin(f"masking '{name}'")

        image = cv2.imread(name)

        mask = get_contour_mask(image)

        resulting = cv2.bitwise_and(image, image, mask=mask)

        tmpfilename = os.path.join(
            tempfile._get_default_tempdir(),
            next(tempfile._get_candidate_names()) + ".jpg"
        )

        cv2.imwrite(tmpfilename, resulting)

        Popen(["exiftool", "-TagsFromFile", name, "-all:all>all:all", tmpfilename],
                stdout=PIPE, stderr=PIPE).communicate()

        os.remove(name)
        shutil.move(tmpfilename, name)

        printer.end("done.")
