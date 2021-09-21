import hashlib
import json
import os
import sys
import tempfile
import urllib
from io import StringIO
from pathlib import Path

import boto3
import botocore
import yaml
import requests


class Versions:
    v2021_4 = "2021.4"
    v2021_3 = "2021.3"
    v2021_2 = "2021.2"
    v2021_1 = "2021.1"
    v2020_4 = "2020.4"
    v2020_3 = "2020.3"
    v2020_2 = "2020.2"
    v2020_1 = "2020.1"
    v2019_R3 = "2019.R3"


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
        fd, path = tempfile.mkstemp()
        data = yaml.dump(self.__config, default_flow_style=False)
        with os.fdopen(fd, 'w') as tmp:
            tmp.write(data)
        return path


__defaults = {
    "url": "http://blobconverter.luxonis.com",
    "version": Versions.v2021_4,
    "shaves": 4,
    "output_dir": Path.home() / Path('.cache/blobconverter'),
    "compile_params": ["-ip U8"],
    "data_type": "FP16",
    "optimizer_params": [
        "--mean_values=[127.5,127.5,127.5]",
        "--scale_values=[255,255,255]",
    ],
    "silent": False,
}
try:
    s3 = boto3.resource('s3', config=botocore.client.Config(signature_version=botocore.UNSIGNED))
    bucket = s3.Bucket('blobconverter')
    s3.meta.client.head_bucket(Bucket=bucket.name)
except botocore.exceptions.EndpointConnectionError:
    # region must be pinned to prevent boto3 specifying a bucket/region that doesn't exist
    s3 = boto3.resource('s3', config=botocore.client.Config(signature_version=botocore.UNSIGNED), region_name='us-east-1')
    bucket = s3.Bucket('blobconverter')
    s3.meta.client.head_bucket(Bucket=bucket.name)


def set_defaults(url=None, version=None, shaves=None, output_dir=None, compile_params: list = None,
                 optimizer_params: list = None, data_type=None, silent=None):
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
    if silent is not None:
        __defaults["silent"] = silent


def show_progress(curr, max):
    done = int(50 * curr / max)
    sys.stdout.write("\r[{}{}]".format('=' * done, ' ' * (50-done)) )
    sys.stdout.flush()


# https://stackoverflow.com/a/54745657/5494277
class __S3ProgressPercentage:
    def __init__(self, o_s3bucket, key_name):
        self._key_name = key_name
        boto_client = o_s3bucket.meta.client
        # ContentLength is an int
        self._size = boto_client.head_object(Bucket=o_s3bucket.name, Key=key_name)['ContentLength']
        self._seen_so_far = 0

    def __call__(self, bytes_amount):
        self._seen_so_far += bytes_amount
        show_progress(self._seen_so_far, self._size)


def __download_from_s3_bucket(key, fpath: Path):
    if __defaults["silent"]:
        bucket.download_file(key, str(fpath.absolute()))
    else:
        progress = __S3ProgressPercentage(bucket, key)
        bucket.download_file(key, str(fpath.absolute()), Callback=progress)
        print()
        print("Done")


def __download_from_response(resp, fpath: Path):
    with fpath.open("wb") as f:
        if 'content-length' not in resp.headers:
                f.write(resp.content)
                return
        total = int(resp.headers.get('content-length', 0))
        dl = 0
        for data in resp.iter_content(chunk_size=4096):
            f.write(data)
            if not __defaults["silent"]:
                dl += len(data)
                show_progress(dl, total)
        if not __defaults["silent"]:
            print()
            print("Done")


def compile_blob(blob_name, version=None, shaves=None, req_data=None, req_files=None, output_dir=None, url=None,
                  use_cache=True, compile_params=None, data_type=None, download_ir=False):
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
    if req_files is None:
        req_files = {}

    blob_path = Path(output_dir) / Path("{}_openvino_{}_{}shave.blob".format(blob_name, version, shaves))
    cache_config_path = Path(__defaults["output_dir"]) / '.config.json'
    if cache_config_path.exists():
        with open(cache_config_path) as f:
            cache_config = {
                key: value for key, value in json.load(f).items() if Path(value).exists()
            }
    else:
        cache_config = {}

    url_params = {
        'version': version,
    }
    data = {
        "myriad_shaves": str(shaves),
        "myriad_params_advanced": ' '.join(compile_params),
        "data_type": data_type,
        "download_ir": download_ir,
        **req_data,
    }

    hash_obj = hashlib.sha256(json.dumps({**url_params, **data}).encode())
    for file_path in req_files.values():
        with open(file_path, 'rb') as f:
            hash_obj.update(f.read())
    req_hash = hash_obj.hexdigest()

    new_cache_config = {
        **cache_config,
        req_hash: str(blob_path),
    }

    if req_hash in cache_config:
        return cache_config[req_hash]

    if blob_path.exists() and use_cache:
        return blob_path

    cache_config_path.parent.mkdir(parents=True, exist_ok=True)
    with cache_config_path.open('w') as f:
        json.dump(new_cache_config, f)

    if not __defaults["silent"]:
        print("Downloading {}...".format(blob_path))

    try:
        if not download_ir:
            __download_from_s3_bucket("{}.blob".format(req_hash), blob_path)
            return blob_path
    except botocore.exceptions.ClientError as ex:
        if ex.response['Error']['Code'] not in ('NoSuchKey', '404'):
            raise ex

    files = {
        name: open(path, 'rb') for name, path in req_files.items()
    }

    response = requests.post(
        "{}/compile?{}".format(url, urllib.parse.urlencode(url_params)),
        data=data,
        files=files,
        stream=True,
    )
    if response.status_code == 400:
        try:
            print(json.dumps(response.json(), indent=4))
        except:
            pass
    response.raise_for_status()

    blob_path.parent.mkdir(parents=True, exist_ok=True)
    if download_ir:
        blob_path = blob_path.with_suffix('.zip')
    __download_from_response(response, blob_path)

    return blob_path


def from_zoo(name, **kwargs):
    body = {
        "name": name,
        "use_zoo": "True",
    }
    return compile_blob(name, req_data=body, **kwargs)


def from_caffe(proto, model, data_type=None, optimizer_params=None, **kwargs):
    if optimizer_params is None:
        optimizer_params = __defaults["optimizer_params"]
    if data_type is None:
        data_type = __defaults["data_type"]
    proto_path = Path(proto)
    model_path = Path(model)
    model_req_name = proto_path.with_suffix('.caffemodel').name

    config_path = ConfigBuilder()\
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
        'config': config_path,
        model_req_name: model_path,
        proto_path.name: proto_path
    }
    body = {
        "name": proto_path.stem,
    }

    return compile_blob(blob_name=proto_path.stem, req_data=body, req_files=files, data_type=data_type, **kwargs)


def from_onnx(model, data_type=None, optimizer_params=None, **kwargs):
    if optimizer_params is None:
        optimizer_params = __defaults["optimizer_params"]
    if data_type is None:
        data_type = __defaults["data_type"]
    model_path = Path(model)

    config_path = ConfigBuilder()\
        .task_type("detection")\
        .framework("onnx")\
        .with_file(model_path.name, model_path)\
        .model_optimizer_args(optimizer_params + [
            "--data_type={}".format(data_type),
            "--input_model=$dl_dir/{}/{}".format(data_type, model_path.name),
        ])\
        .build()
    files = {
        'config': config_path,
        model_path.name: model_path
    }
    body = {
        "name": model_path.stem,
    }

    return compile_blob(blob_name=model_path.stem, req_data=body, req_files=files, data_type=data_type, **kwargs)


def from_tf(frozen_pb, data_type=None, optimizer_params=None, **kwargs):
    if optimizer_params is None:
        optimizer_params = __defaults["optimizer_params"]
    if data_type is None:
        data_type = __defaults["data_type"]
    frozen_pb_path = Path(frozen_pb)

    config_path = ConfigBuilder()\
        .task_type("detection")\
        .framework("tf")\
        .with_file(frozen_pb_path.name, frozen_pb_path)\
        .model_optimizer_args(optimizer_params + [
            "--data_type={}".format(data_type),
            "--input_model=$dl_dir/{}/{}".format(data_type, frozen_pb_path.name),
        ])\
        .build()
    files = {
        'config': config_path,
        frozen_pb_path.name: frozen_pb_path
    }
    body = {
        "name": frozen_pb_path.stem,
    }

    return compile_blob(blob_name=frozen_pb_path.stem, req_data=body, req_files=files, data_type=data_type, **kwargs)


def from_openvino(xml, bin, **kwargs):
    xml_path = Path(xml)
    bin_path = Path(bin)
    bin_req_name = xml_path.with_suffix('.bin').name

    config_path = ConfigBuilder()\
        .task_type("detection")\
        .framework("dldt")\
        .with_file(xml_path.name, xml_path)\
        .with_file(bin_req_name, bin_path)\
        .build()
    files = {
        'config': config_path,
        xml_path.name: xml_path,
        bin_req_name: bin_path
    }

    body = {
        "name": xml_path.stem,
    }

    return compile_blob(blob_name=xml_path.stem, req_data=body, req_files=files, **kwargs)


def from_config(name, path, **kwargs):
    body = {
        "name": name,
        "use_zoo": "True",
    }
    files = {
        'config': path,
    }
    return compile_blob(blob_name=name, req_data=body, req_files=files, **kwargs)


def zoo_list(version=None, url=None):
    if url is None:
        url = __defaults["url"]
    if version is None:
        version = __defaults["version"]

    url_params = {
        'version': version
    }

    response = requests.get("{}/zoo_models?{}".format(url, urllib.parse.urlencode(url_params)))
    response.raise_for_status()
    return response.json()['available']



def __run_cli__():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-zn', '--zoo-name', help="Name of a model to download from OpenVINO Model Zoo")
    parser.add_argument('-onnx', '--onnx-model', help="Path to ONNX .onnx file")
    parser.add_argument('-cp', '--caffe-proto', help="Path to Caffe .prototxt file")
    parser.add_argument('-cm', '--caffe-model', help="Path to Caffe .caffemodel file")
    parser.add_argument('-tf', '--tensorflow-pb', help="Path to TensorFlow .pb file")
    parser.add_argument('-ox', '--openvino-xml', help="Path to OpenVINO .xml file")
    parser.add_argument('-ob', '--openvino-bin', help="Path to OpenVINO .bin file")
    parser.add_argument('-rawn', '--raw-name', help="Name of the converted model (advanced)")
    parser.add_argument('-rawc', '--raw-config', help="Path to raw .yml file with model config (advanced)")
    parser.add_argument('-sh', '--shaves', type=int, default=4, choices=range(1, 17), help="Specifies number of SHAVE cores that converted model will use")
    parser.add_argument('-dt', '--data-type', help="Specifies model data type")
    parser.add_argument('-o', '--output-dir', help="Directory where the output blob should be saved")
    parser.add_argument('-v', '--version', help="OpenVINO version to use for conversion")
    parser.add_argument('--optimizer-params', help="Additional params to use when converting a model to OpenVINO IR")
    parser.add_argument('--compile-params', help="Additional params to use when compiling a model to MyriadX blob")
    parser.add_argument('--converter-url', dest="url", help="URL to BlobConverter API endpoint used for conversion")
    parser.add_argument('--no-cache', dest="use_cache", action="store_false", help="Omit .cache directory and force new compilation of the blob")
    parser.add_argument('--zoo-list', action="store_true", help="List all models available in OpenVINO Model Zoo")
    parser.add_argument('--download-ir', action="store_true", help="Downloads OpenVINO IR files used to compile the blob. Result path points to a result ZIP archive")

    args = parser.parse_args()

    optimizer_params = ['--' + param.strip() for param in args.optimizer_params.split('--') if param] if args.optimizer_params else []

    common_args = {
        arg: getattr(args, arg)
        for arg in ["shaves", "data_type", "output_dir", "version", "url", "compile_params", "download_ir"]
    }
    if args.zoo_list:
        return zoo_list()

    if args.zoo_name:
        return from_zoo(
            name=args.zoo_name,
            **common_args
        )
    if args.caffe_proto or args.caffe_model:
        if None in (args.caffe_proto, args.caffe_model):
            raise ValueError("Both Caffe proto and model needs to be supplied!")

        return from_caffe(
            proto=args.caffe_proto,
            model=args.caffe_model,
            optimizer_params=optimizer_params,
            **common_args
        )
    if args.tensorflow_pb:
        return from_tf(
            frozen_pb=args.tensorflow_pb,
            optimizer_params=optimizer_params,
            **common_args
        )
    if args.onnx_model:
        return from_onnx(
            model=args.onnx_model,
            optimizer_params=optimizer_params,
            **common_args
        )
    if args.openvino_xml or args.openvino_bin:
        if None in (args.openvino_xml, args.openvino_bin):
            raise ValueError("Both OpenVINO xml and bin needs to be supplied!")

        return from_openvino(
            xml=args.openvino_xml,
            bin=args.openvino_bin,
            **common_args
        )
    if args.raw_config or args.raw_name:
        if None in (args.raw_config, args.raw_name):
            raise ValueError("Both raw config and name needs to be supplied!")

        return from_config(args.raw_name, args.raw_config)

    raise RuntimeError("No conversion source specified!")


if __name__ == "__main__":
    print(__run_cli__())
