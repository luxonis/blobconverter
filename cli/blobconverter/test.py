import subprocess
import sys
import shutil
from pathlib import Path
import blobconverter

use_cache = False

if not use_cache and Path(blobconverter.__defaults["output_dir"]).exists():
    shutil.rmtree(blobconverter.__defaults["output_dir"])

result = blobconverter.from_zoo(name="mobilenet-ssd", use_cache=use_cache)
print(result)

result = blobconverter.from_openvino(
    xml="../../face-detection-retail-0004.xml",  # get from https://storage.openvinotoolkit.org/repositories/open_model_zoo/2021.2/models_bin/3/face-detection-retail-0004/FP16/face-detection-retail-0004.xml
    bin="../../face-detection-retail-0004.bin",  # get from https://storage.openvinotoolkit.org/repositories/open_model_zoo/2021.2/models_bin/3/face-detection-retail-0004/FP16/face-detection-retail-0004.bin
    data_type="FP16",
    shaves=5,
    use_cache=use_cache,
)
print(result)

result = blobconverter.from_openvino(
    xml="face-detection-retail-0004.xml",  # get from https://storage.openvinotoolkit.org/repositories/open_model_zoo/2021.2/models_bin/3/face-detection-retail-0004/FP16/face-detection-retail-0004.xml
    bin="face-detection-retail-0004.bin",  # get from https://storage.openvinotoolkit.org/repositories/open_model_zoo/2021.2/models_bin/3/face-detection-retail-0004/FP16/face-detection-retail-0004.bin
    data_type="FP16",
    shaves=5,
    use_cache=use_cache,
)
print(result)

result = blobconverter.from_zoo(name="megadepth", zoo_type="depthai")
print(result)

result = blobconverter.from_openvino(
    xml="https://storage.openvinotoolkit.org/repositories/open_model_zoo/2021.4/models_bin/3/age-gender-recognition-retail-0013/FP16/age-gender-recognition-retail-0013.xml",
    xml_size=31526,
    xml_sha256="54d62ce4a3c3d7f1559a22ee9524bac41101103a8dceaabec537181995eda655",
    bin="https://storage.openvinotoolkit.org/repositories/open_model_zoo/2021.4/models_bin/3/age-gender-recognition-retail-0013/FP16/age-gender-recognition-retail-0013.bin",
    bin_size=4276038,
    bin_sha256="3586df5340e9fcd73ba0e2d802631bd9e027179490635c03b273d33d582e2b58"
)
print(result)

result = blobconverter.from_onnx(
    model="../../concat.onnx",
    shaves=3,
    use_cache=use_cache,
    optimizer_params=[],
    data_type="FP16"
)
print(result)

result = blobconverter.from_zoo(
    name="face-detection-retail-0004",
    shaves=3,
    use_cache=use_cache
)
print(result)

result = blobconverter.from_caffe(
    proto="../../mobilenet-ssd.prototxt",  # get from https://raw.githubusercontent.com/chuanqi305/MobileNet-SSD/ba00fc987b3eb0ba87bb99e89bf0298a2fd10765/MobileNetSSD_deploy.prototxt
    model="../../mobilenet-ssd.caffemodel",  # get from https://drive.google.com/file/d/0B3gersZ2cHIxRm5PMWRoTkdHdHc
    data_type="FP16",
    shaves=5,
    use_cache=use_cache,
)
print(result)

result = blobconverter.from_tf(
    frozen_pb="../../deeplabv3_mnv2_pascal_train_aug.pb",  # get from http://download.tensorflow.org/models/deeplabv3_mnv2_pascal_train_aug_2018_01_29.tar.gz
    data_type="FP16",
    shaves=5,
    optimizer_params=[
        "--reverse_input_channels",
        "--input_shape=[1,513,513,3]",
        "--input=1:mul_1",
        "--output=ArgMax",
    ],
    use_cache=use_cache,
)
print(result)

result = blobconverter.from_config(
    name="license-plate-recognition-barrier-0001",  # https://raw.githubusercontent.com/openvinotoolkit/open_model_zoo/master/models/intel/license-plate-recognition-barrier-0001/model.yml
    path="../../model.yml",
    data_type="FP16",
    shaves=5,
    use_cache=use_cache
)
print(result)

subprocess.check_call([sys.executable, "__init__.py", "--zoo-name", "face-detection-retail-0004", "--shaves", "6"] + ([] if use_cache else ['--no-cache']))
subprocess.check_call([sys.executable, "__init__.py", "--caffe-proto", "../../mobilenet-ssd.prototxt", "--caffe-model", "../../mobilenet-ssd.caffemodel", "--shaves", "6"] + ([] if use_cache else ['--no-cache']))
subprocess.check_call([sys.executable, "__init__.py", "--tensorflow-pb", "../../deeplabv3_mnv2_pascal_train_aug.pb", "--optimizer-params", "--reverse_input_channels --input_shape=[1,513,513,3] --input=1:mul_1 --output=ArgMax", "--shaves", "6"] + ([] if use_cache else ['--no-cache']))
subprocess.check_call([sys.executable, "__init__.py", "--openvino-xml", "../../face-detection-retail-0004.xml", "--openvino-bin", "../../face-detection-retail-0004.bin", "--shaves", "7"] + ([] if use_cache else ['--no-cache']))
subprocess.check_call([sys.executable, "__init__.py", "--raw-config", "../../model.yml", "--raw-name", "license-plate-recognition-barrier-0001", "--shaves", "6"] + ([] if use_cache else ['--no-cache']))
