"""Add holds that were not yet added to the dictionary."""
import os
import sys
import hashlib
import math
import datetime
from subprocess import Popen, PIPE, DEVNULL
from PIL import Image, ImageEnhance
from glob import glob

import matplotlib.pyplot as plt
import numpy as np

sys.path.append("..")
from config import *
from utilities import *

os.chdir(os.path.dirname(os.path.abspath(__file__)))

from yaml import load, dump
from yaml import CLoader as Loader, CDumper as Dumper

printer = Printer("model")

import argparse

parser = argparse.ArgumentParser()

parser.add_argument("-m", "--mode",
    help="The mode of the color inference ('manual' or 'automatic'). Defaults to 'manual', since automatic is quite unreliable.",
    choices=["manual", "automatic"],
    default="manual"
)

arguments = parser.parse_args()

def get_file_hashsum(path, characters=12):
    """Return the hashsum of the file contents."""
    with open(path) as f:
        return hashlib.sha256(f.read().encode("utf-8")).hexdigest()[:12]


def manual_infer_texture_color(path, default_color=None):
    """Infer a color from a jpg texture of the file manually (asking the user)."""
    img = Image.open(path)

    # https://newbedev.com/plotting-in-a-non-blocking-way-with-matplotlib
    plt.imshow(np.asarray(img))
    plt.ion()
    plt.show()
    plt.draw()
    plt.pause(0.001)

    if default_color is not None:
        printer.mid(f"input image color (defaults to '{default_color}'): ", dots=False)
    else:
        printer.mid("input image color: ", dots=False)

    color = input().strip().lower()

    printer.begin("confirmed")

    while True:
        if color in [c for c in NAMED_COLORS]:
            break

        if color == "" and default_color is not None:
            color = default_color
            break

        printer.begin(f"color '{color}' not recognized, try again: ", dots=False)
        color = input().strip().lower()

    plt.close()

    return color


def automatic_infer_texture_color(path):
    """Infer a color from a jpg texture of the file automatically."""

    def hex_to_tuple(color):
        """Return an (r, g, b) tuple from a hex string."""
        return tuple([int(color[1:][i * 2 : (i + 1) * 2], 16) for i in range(3)])

    def get_average_color(path, enhance=4):
        """Given a path to image, return average value of color as (r, g, b).
        Also saturates it for the color to be more vivid."""
        i_orig = Image.open(path)

        converter = ImageEnhance.Color(i_orig)
        i = converter.enhance(enhance)
        h = i.histogram()

        # split into red, green, blue
        r = h[0:256]
        g = h[256:256*2]
        b = h[256*2: 256*3]

        # perform the weighted average of each channel:
        # the *index* is the channel value, and the *value* is its weight
        return (
            sum( i*w for i, w in enumerate(r) ) / sum(r),
            sum( i*w for i, w in enumerate(g) ) / sum(g),
            sum( i*w for i, w in enumerate(b) ) / sum(b)
        )

    def color_distance(c1, c2):
        """Return the distance between two colors (in Euclidean distance)."""
        return math.sqrt(sum([(x1 - x2) ** 4 for x1, x2 in zip(c1, c2)]))

    average_color = get_average_color(path)

    # return the closest named color
    min_color_distance = float("inf")
    min_color = None
    for name, color in NAMED_COLORS.items():
        distance = color_distance(hex_to_tuple(color), average_color)
        if distance < min_color_distance:
            min_color_distance = distance
            min_color = name

    return min_color


def file_modification_date(path):
    """Get the file modification time."""
    return datetime.datetime.fromtimestamp(os.path.getmtime(path))


model_yaml_path = os.path.join(MODEL_PATH, MODEL_YAML_NAME)

if not os.path.exists(MODEL_PATH):
    os.mkdir(MODEL_PATH)

if not os.path.exists(model_yaml_path):
    data = {}
else:
    with open(model_yaml_path) as f:
        # if the file is empty, None is read; we want an empty dict instead
        data = load(f.read(), Loader=Loader) or {}

previous_color = None
for model_folder in sorted(glob(os.path.join(MODEL_PATH, "*"))):
    # skip files
    if not os.path.isdir(model_folder):
        continue

    hold_path = os.path.join(model_folder, MODEL_FILE_NAME + ".obj")
    texture_path = os.path.join(model_folder, MODEL_FILE_NAME + ".jpg")

    printer.begin(f"reading '{hold_path}'")
    try:
        id = get_file_hashsum(hold_path)
    except FileNotFoundError:
        printer.end(f"doesn't contain {MODEL_FILE_NAME + '.obj'}, skipping.")
        continue

    if id not in data:
        data[id] = {}

        # infer color by parsing the texture file
        if arguments.mode == "automatic":
            color = automatic_infer_texture_color(texture_path)
        else:
            color = manual_infer_texture_color(texture_path, previous_color)
            previous_color = color

        if color is None:
            printer.mid("no color information")
        else:
            data[id]["color"] = [color, NAMED_COLORS[color]]
            printer.mid(f"color {color} inferred")

        # add modification date
        data[id]["date"] = file_modification_date(hold_path)

        # add volume
        result = Popen(["python3", "02-get-volume.py", f"{os.path.join(model_folder, MODEL_FILE_NAME)}.obj"],
                stdout=PIPE, stderr=DEVNULL).communicate()

        data[id]["volume"] = float(result[0].decode())

        printer.end(f"added.")
    else:
        printer.end(f"already added, skipping.")

with open(model_yaml_path, "w") as f:
    f.write(dump(data, Dumper=Dumper))
