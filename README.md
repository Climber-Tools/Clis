<p align="center" width="100%">
<img width="50%" src="https://raw.githubusercontent.com/Climber-Apps/Clis/master/logo.svg">
</p>

<p align="center" width="100%">
The <strong>cli</strong>mber's <strong>s</strong>canner – efficient 3D scanning of climbing holds and climbing gym interiors.
</p>

## Introduction
This project contains everything you need to efficiently scan large set of holds (or other 3D objects, for that matter, if forked and adjusted accordingly) in a small amount of time. It uses an Arduino-powered turntable and camera to automatically take pictures, which it then converts to 3D models using the [Agisoft Metashape](https://www.agisoft.com/) photogrammetry software.

Additionally, it contains a tutorial for scanning climbing gym interiors, both of which can then be used in [Cled – the climber's editor](https://github.com/Climber-Apps/Cled).

## Setting up
For the setup, you'll need to first install `pyenv`:

```
curl https://pyenv.run | bash
```

and configure your shell's environment: https://github.com/pyenv/pyenv#basic-github-checkout

You'll then need to install Python `3.7.x` (due to Metashape and Blender working only with older Python versions):

```
pyenv install -v 3.7.12
```

To set up the virtual environment, do (in this directory)

```
pyenv virtualenv 3.7.12 clis
pyenv local clis
pyenv activate clis
pyenv exec pip install -r requirements.txt
pyenv exec bpy_post_install
```

## Contents
Before running the scripts (using `pyenv exec`), it is advisable to check `config.py`, since a lot of the values will most likely differ from their default values for your particular setup. Each of the respective folders contain a `README.md` that further explains the usage of each of the scripts.

### `01-scanning/`
Contains tools for scanning the holds.

### `02-processing/`
Contains tools for processing the hold images into 3D models.

### `03-data/`
Contains the hold data format specification and tools for managing the 3D models.

## Sample usage
Run 

```
pyenv exec python 01-scanning/01-scan.py automatic 15 && pyenv exec python 01-scanning/02-copy.py camera && pyenv exec python 01-scanning/03-convert.py
```

to automatically take 15 pictures of the hold, copy it from the camera and convert it from raw. If you want to take them manually because you don't have the turntable, replace `automatic` with `manual`. Then run

```
pyenv exec python 02-processing/01-model.py
```

To generate the model. Finally, run

```
pyenv exec python 03-data/01-add_models.py
```

To add the information about the hold to the `holds.yaml` dictionary.
