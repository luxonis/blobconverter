import urllib
from io import StringIO
from pathlib import Path
import yaml
import requests
import pprint


class Versions:
    v2021_2 = "2021.2"
    v2021_1 = "2021.1"
    v2020_4 = "2020.4"
    v2020_3 = "2020.3"
    v2020_2 = "2020.2"
    v2020_1 = "2020.1"
    v2019_R3 = "2019.R3"

"""
task_type: detection
files: 
  - name: FP16/mobilenet.caffemodel
    source:
      $type: http
      url: $REQUEST/mobilenet.caffemodel
  - name: FP16/mobilenet.prototxt
    source:
      $type: http
      url: $REQUEST/mobilenet.prototxt
framework: caffe
model_optimizer_args:
  - --data_type=FP16
  - --mean_values=[127.5,127.5,127.5]
  - --scale_values=[255,255,255]
  - --input_model=$dl_dir/FP16/mobilenet.caffemodel
  - --input_proto=$dl_dir/FP16/mobilenet.prototxt"""


class ConfigBuilder:
    def __init__(self, precision="FP16"):
        self.precision = precision
        self.__config = {"files": []}

    def task_type(self, task_type):
        self.__config["task_type"] = task_type
        return self

    def framework(self, framework):
        self.__config["framework"] = framework
        return self

    def model_optimizer_args(self, args: list):
        self.__config["model_optimizer_args"] = args
        return self

    def with_file(self, name, path=None, url=None, google_drive=None, size=None, sha256=None):
        file_entry = {
            "name": "{}/{}".format(self.precision, name),
        }

        if path is not None:
            file_path = Path(path)
            if not path.exists():
                raise FileNotFoundError(file_path)
            file_entry["source"] = {
                "$type": "http",
                "url": "$REQUEST/{}".format(file_path.name)
            }
        elif size is None or sha256 is None:
            raise RuntimeError(
                "Both \"size\" and \"sha256\" params must be provided! (can only be omitted if using \"path\" param)"
            )
        elif url is not None:
            file_entry["source"] = url
            file_entry["size"] = size
            file_entry["sha256"] = sha256
        elif google_drive is not None:
            file_entry["source"] = {
                "$type": "google_drive",
                "id": google_drive
            }
            file_entry["size"] = size
            file_entry["sha256"] = sha256
        else:
            raise RuntimeError("No file source specified!")

        self.__config["files"].append(file_entry)
        return self

    def build(self):
        return yaml.dump(self.__config, default_flow_style=False)


__defaults = {
    "url": "http://69.164.214.171:8084/compile",
    "version": Versions.v2021_2,
    "shaves": 4,
    "output_dir": Path('.cache/blobconverter'),
    "compile_params": ["-ip U8"],
    "data_type": "FP16",
    "optimizer_params": [
        "--mean_values=[127.5,127.5,127.5]",
        "--scale_values=[255,255,255]",
    ],
}


def set_defaults(url=None, version=None, shaves=None, output_dir=None, compile_params: list = None,
                 optimizer_params: list = None, data_type=None):
    if url is not None:
        __defaults["url"] = url
    if version is not None:
        __defaults["version"] = version
    if shaves is not None:
        __defaults["shaves"] = shaves
    if output_dir is not None:
        __defaults["output_dir"] = output_dir
    if compile_params is not None:
        __defaults["compile_params"] = compile_params
    if optimizer_params is not None:
        __defaults["optimizer_params"] = optimizer_params
    if data_type is not None:
        __defaults["data_type"] = data_type


def compile_blob(blob_name, version=None, shaves=None, req_data=None, req_files=None, output_dir=None, url=None,
                  use_cache=True, compile_params=None, data_type=None):
    if shaves is None:
        shaves = __defaults["shaves"]
    if url is None:
        url = __defaults["url"]
    if version is None:
        version = __defaults["version"]
    if output_dir is None:
        output_dir = __defaults["output_dir"]
    if compile_params is None:
        compile_params = __defaults["compile_params"]
    if data_type is None:
        data_type = __defaults["data_type"]

    blob_path = Path(output_dir) / Path("{}_openvino_{}_{}shave.blob".format(blob_name, version, shaves))
    if blob_path.exists() and use_cache:
        return blob_path

    url_params = {
        'version': version
    }
    data = {
        "myriad_shaves": shaves,
        "myriad_params_advanced": compile_params,
        "data_type": data_type,
        **req_data,
    }
    response = requests.post("{}?{}".format(url, urllib.parse.urlencode(url_params)), data=data, files=req_files)
    if response.status_code == 400:
        try:
            pprint.pprint(response.json())
        except:
            pass
    response.raise_for_status()

    blob_path.parent.mkdir(parents=True, exist_ok=True)
    with blob_path.open("wb") as f:
        f.write(response.content)

    return blob_path


def from_zoo(name, **kwargs):
    body = {
        "name": name,
        "use_zoo": True,
    }
    return compile_blob(name, req_data=body, **kwargs)


def from_caffe(proto, model, data_type, optimizer_params=None, **kwargs):
    if optimizer_params is None:
        optimizer_params = __defaults["optimizer_params"]
    proto_path = Path(proto)
    model_path = Path(model)
    model_req_name = proto_path.with_suffix('.caffemodel').name

    config = ConfigBuilder()\
        .task_type("detection")\
        .framework("caffe")\
        .with_file(proto_path.name, proto_path)\
        .with_file(model_req_name, model_path)\
        .model_optimizer_args(optimizer_params + [
            "--data_type={}".format(data_type),
            "--input_model=$dl_dir/{}/{}".format(data_type, model_req_name),
            "--input_proto=$dl_dir/{}/{}".format(data_type, proto_path.name),
        ])\
        .build()
    files = {
        'config': StringIO(config),
        model_req_name: open(model_path, 'rb'),
        proto_path.name: open(proto_path, 'rb')
    }
    body = {
        "name": proto_path.stem,
    }

    return compile_blob(blob_name=proto_path.stem, req_data=body, req_files=files, data_type=data_type, **kwargs)


def from_tf(frozen_pb, data_type, optimizer_params=None, **kwargs):
    if optimizer_params is None:
        optimizer_params = __defaults["optimizer_params"]
    frozen_pb_path = Path(frozen_pb)

    config = ConfigBuilder()\
        .task_type("detection")\
        .framework("tf")\
        .with_file(frozen_pb_path.name, frozen_pb_path)\
        .model_optimizer_args(optimizer_params + [
            "--data_type={}".format(data_type),
            "--input_model=$dl_dir/{}/{}".format(data_type, frozen_pb_path.name),
        ])\
        .build()
    files = {
        'config': StringIO(config),
        frozen_pb_path.name: open(frozen_pb_path, 'rb')
    }
    body = {
        "name": frozen_pb_path.stem,
    }

    return compile_blob(blob_name=frozen_pb_path.stem, req_data=body, req_files=files, data_type=data_type, **kwargs)


def from_openvino(xml, bin, data_type, **kwargs):
    xml_path = Path(xml)
    bin_path = Path(bin)
    bin_req_name = xml_path.with_suffix('.bin').name

    config = ConfigBuilder()\
        .task_type("detection")\
        .framework("dldt")\
        .with_file(xml_path.name, xml_path)\
        .with_file(bin_req_name, bin_path)\
        .build()
    files = {
        'config': StringIO(config),
        xml_path.name: open(xml_path, 'rb'),
        bin_req_name: open(bin_path, 'rb')
    }
    body = {
        "name": xml_path.stem,
    }

    return compile_blob(blob_name=xml_path.stem, req_data=body, req_files=files, data_type=data_type, **kwargs)


def __run_cli__():
    print("test")


if __name__ == "__main__":
    __run_cli__()
