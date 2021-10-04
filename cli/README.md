# BlobConverter CLI

This tool allows you to convert neural network files (from various sources, like Tensorflow, Caffe or OpenVINO) 
to MyriadX blob file

## Installation

```
python3 -m pip install blobconverter
```
## Usage

```
usage: blobconverter [-h] [-zn ZOO_NAME] [-zt ZOO_TYPE] [-onnx ONNX_MODEL] [-cp CAFFE_PROTO] [-cm CAFFE_MODEL] [-tf TENSORFLOW_PB] [-ox OPENVINO_XML] [-ob OPENVINO_BIN]
                     [-rawn RAW_NAME] [-rawc RAW_CONFIG] [-sh {1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16}] [-dt DATA_TYPE] [-o OUTPUT_DIR] [-v VERSION]
                     [--optimizer-params OPTIMIZER_PARAMS] [--compile-params COMPILE_PARAMS] [--converter-url URL] [--no-cache] [--zoo-list] [--download-ir]

optional arguments:
  -h, --help            show this help message and exit
  -zn ZOO_NAME, --zoo-name ZOO_NAME
                        Name of a model to download from OpenVINO Model Zoo
  -zt ZOO_TYPE, --zoo-type ZOO_TYPE
                        Type of the model zoo to use, available: "intel", "depthai"
  -onnx ONNX_MODEL, --onnx-model ONNX_MODEL
                        Path to ONNX .onnx file
  -cp CAFFE_PROTO, --caffe-proto CAFFE_PROTO
                        Path to Caffe .prototxt file
  -cm CAFFE_MODEL, --caffe-model CAFFE_MODEL
                        Path to Caffe .caffemodel file
  -tf TENSORFLOW_PB, --tensorflow-pb TENSORFLOW_PB
                        Path to TensorFlow .pb file
  -ox OPENVINO_XML, --openvino-xml OPENVINO_XML
                        Path to OpenVINO .xml file
  -ob OPENVINO_BIN, --openvino-bin OPENVINO_BIN
                        Path to OpenVINO .bin file
  -rawn RAW_NAME, --raw-name RAW_NAME
                        Name of the converted model (advanced)
  -rawc RAW_CONFIG, --raw-config RAW_CONFIG
                        Path to raw .yml file with model config (advanced)
  -sh {1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16}, --shaves {1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16}
                        Specifies number of SHAVE cores that converted model will use
  -dt DATA_TYPE, --data-type DATA_TYPE
                        Specifies model data type
  -o OUTPUT_DIR, --output-dir OUTPUT_DIR
                        Directory where the output blob should be saved
  -v VERSION, --version VERSION
                        OpenVINO version to use for conversion
  --optimizer-params OPTIMIZER_PARAMS
                        Additional params to use when converting a model to OpenVINO IR
  --compile-params COMPILE_PARAMS
                        Additional params to use when compiling a model to MyriadX blob
  --converter-url URL   URL to BlobConverter API endpoint used for conversion
  --no-cache            Omit .cache directory and force new compilation of the blob
  --zoo-list            List all models available in OpenVINO Model Zoo
  --download-ir         Downloads OpenVINO IR files used to compile the blob. Result path points to a result ZIP archive
```

## Conversion examples (cli)

### OpenVINO Model Zoo

```
python3 -m blobconverter --zoo-name face-detection-retail-0004 --shaves 6
```

To list all available models, run

```
python3 -m blobconverter --zoo-list
```

### Caffe

```
python3 -m blobconverter --caffe-proto /path/to/mobilenet-ssd.prototxt --caffe-model /path/to/mobilenet-ssd.caffemodel --shaves 6
```


### TensorFlow

```
python3 -m blobconverter --tensorflow-pb /path/to/deeplabv3_mnv2_pascal_train_aug.pb --optimizer-params --reverse_input_channels --input_shape=[1,513,513,3] --input=1:mul_1 --output=ArgMax --shaves 6
```


### ONNX

```
python3 -m blobconverter --onnx-model /path/to/model.onnx --shaves 6
```


### OpenVINO IR

```
python3 -m blobconverter --openvino-xml /path/to/face-detection-retail-0004.xml --openvino-bin /path/to/face-detection-retail-0004.bin --shaves 7
```


### Raw model config (advanced)

```
python3 -m blobconverter --raw-config /path/to/model.yml --raw-name license-plate-recognition-barrier-0007 --shaves 6
```

## Conversion examples (Python)

### OpenVINO Model Zoo

```python
import blobconverter

blob_path = blobconverter.from_zoo(
    name="face-detection-retail-0004", 
    shaves=6,
)
```

To get all available models, use

```python
import blobconverter

available_models = blobconverter.zoo_list()
```

### Caffe

```python
import blobconverter

blob_path = blobconverter.from_caffe(
    proto="/path/to/mobilenet-ssd.prototxt",
    model="/path/to/mobilenet-ssd.caffemodel",
    data_type="FP16",
    shaves=5,
)
```


### TensorFlow

```python
import blobconverter

blob_path = blobconverter.from_tf(
    frozen_pb="/path/to/deeplabv3_mnv2_pascal_train_aug.pb",
    data_type="FP16",
    shaves=5,
    optimizer_params=[
        "--reverse_input_channels",
        "--input_shape=[1,513,513,3]",
        "--input=1:mul_1",
        "--output=ArgMax",
    ],
)
```

### ONNX

```python
import blobconverter

blob_path = blobconverter.from_onnx(
    model="/path/to/model.onnx",
    data_type="FP16",
    shaves=5,
)
```


### OpenVINO IR

```python
import blobconverter

blob_path = blobconverter.from_openvino(
    xml="/path/to/face-detection-retail-0004.xml",
    bin="/path/to/face-detection-retail-0004.bin",
    data_type="FP16",
    shaves=5,
)
```


### Raw model config (advanced)

```python
import blobconverter

blob_path = blobconverter.from_config(
    name="license-plate-recognition-barrier-0007",
    path="/path/to/model.yml",
    data_type="FP16",
    shaves=5,
)
```

### Use [DepthAI Model Zoo](https://github.com/luxonis/depthai-model-zoo) to download files

```python
import blobconverter

blob_path = blobconverter.from_zoo(name="megadepth", zoo_type="depthai")
```

### Download using URLs instead of local files
```python
import blobconverter

blob_path = blobconverter.from_openvino(
    xml="https://storage.openvinotoolkit.org/repositories/open_model_zoo/2021.4/models_bin/3/age-gender-recognition-retail-0013/FP16/age-gender-recognition-retail-0013.xml",
    xml_size=31526,
    xml_sha256="54d62ce4a3c3d7f1559a22ee9524bac41101103a8dceaabec537181995eda655",
    bin="https://storage.openvinotoolkit.org/repositories/open_model_zoo/2021.4/models_bin/3/age-gender-recognition-retail-0013/FP16/age-gender-recognition-retail-0013.bin",
    bin_size=4276038,
    bin_sha256="3586df5340e9fcd73ba0e2d802631bd9e027179490635c03b273d33d582e2b58"
)
```
