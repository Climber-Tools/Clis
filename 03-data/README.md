# Data

## Specification
The specification of the data format used for the climbing holds and the climbing wall:

```yaml
<sha256sum of the file contents (the first 12 characters)>:
  color: [<name of the color>, <hex value of the color>]
  type: <the type of hold (like crimp, jug, sloper, pinch, pocket, foothold, structure, etc.)>
  date: <the date the hold model was created>
  manufacturer: <the name of the manufacturer>
  labels: [<list>, <of>, <custom>, <labels>]
  volume: <a float volume of the hold>
```

## `01-add_models.py`
A script for adding the generated holds into the `holds.yaml` dictionary, automatically inferring their color from the texture in the process.

## `02-get-volume.py`
Calculate the volume of the given `obj` file, printing it to standard output.

