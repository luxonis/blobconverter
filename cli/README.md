# Blobconverter CLI

This tool allows you to convert neural network files (from various sources, like Tensorflow, Caffe or OpenVINO) 
to MyriadX blob file

## Installation

```
python3 -m pip install blobconverter
```
## Usage

```
usage: blobconverter [-h] [-sh]

optional arguments:
  -h, --help            show this help message and exit
  -sh, --shaves         how many SHAVEs will be assigned to blob file
```

To convert a model in OpenVINO IR format, run
```
blobconverter -sh 8 
```
