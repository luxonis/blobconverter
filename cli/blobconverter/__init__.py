import hashlib
import json
import os
import struct
import sys
import tempfile
import urllib
from os import path
from pathlib import Path

import requests
import yaml


class Versions:
    v2022_3_RVC3 = "2022.3_RVC3"
    v2022_1 = "2022.1"
    v2021_4 = "2021.4"
    v2021_3 = "2021.3"
    v2021_2 = "2021.2"


def get_filename(url):
    fragment_removed = url.split("#")[0]  # keep to left of first #
    query_string_removed = fragment_removed.split("?")[0]
    scheme_removed = query_string_removed.split("://")[-1].split(":")[-1]

    return path.basename(scheme_removed)


def show_progress(curr, max):
    done = int(50 * curr / max)
    sys.stdout.write("\r[{}{}]".format('=' * done, ' ' * (50 - done)))
    sys.stdout.flush()


def is_valid_name(name):
    return name.count(".") <= 1 and name.count("=") == 0


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
        elif url is not None:
            file_entry["source"] = url
            if size is not None:
                file_entry["size"] = size
            if sha256 is not None:
                file_entry["sha256"] = sha256
        elif google_drive is not None:
            file_entry["source"] = {
                "$type": "google_drive",
                "id": google_drive
            }
            if size is not None:
                file_entry["size"] = size
            if sha256 is not None:
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
    "url": "https://blobconverter.luxonis.com",
    "version": Versions.v2022_1,
    "shaves": 4,
    "output_dir": Path.home() / Path('.cache/blobconverter'),
    "compile_params": ["-ip U8"],
    "data_type": "FP16",
    "optimizer_params": [
        "--mean_values=[127.5,127.5,127.5]",
        "--scale_values=[255,255,255]",
    ],
    "progress_func": show_progress,
    "silent": False,
    "zoo_type": "intel",
}

s3 = None
bucket = None


def __init_s3():
    global s3, bucket
    try:
        s3 = boto3.resource('s3', config=botocore.client.Config(signature_version=botocore.UNSIGNED))
        bucket = s3.Bucket('blobconverter')
        s3.meta.client.head_bucket(Bucket=bucket.name)
    except botocore.exceptions.EndpointConnectionError:
        # Region must be pinned to prevent boto3 specifying a bucket/region that doesn't exist
        s3 = boto3.resource('s3', config=botocore.client.Config(signature_version=botocore.UNSIGNED), region_name='us-east-1')
        bucket = s3.Bucket('blobconverter')
        s3.meta.client.head_bucket(Bucket=bucket.name)


def set_defaults(url=None, version=None, shaves=None, output_dir=None, compile_params: list = None,
                 optimizer_params: list = None, data_type=None, silent=None, zoo_type=None, progress_func=None):
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
    if zoo_type is not None:
        __defaults["zoo_type"] = zoo_type
    if progress_func is not None:
        __defaults["progress_func"] = progress_func


def is_valid_blob(blob_path):
    convertedPath = Path(blob_path)
    if not convertedPath.exists():
        return False

    try:
        with convertedPath.open('rb+') as f:
            f.seek(52)
            magic_number = struct.unpack("<I", f.read(4))[0]  # `<` means little endian, `I` means unsigned int 4 bytes
            f.seek(56)
            expected_size = struct.unpack("<I", f.read(4))[0]  # `<` means little endian, `I` means unsigned int 4 bytes
            f.seek(0, os.SEEK_END)
            actual_size = f.tell()
            return expected_size <= actual_size and magic_number == 9709
    except:
        return False


def __download_file_from_url(file_url, save_path):
    response = requests.get(file_url)

    if response.status_code == 200:
        with open(save_path, 'wb') as file:
            file.write(response.content)
    else:
        raise FileNotFoundError(f"File not found at {file_url}")


def __download_from_s3_bucket(key, fpath: Path):
    url = f'https://blobconverter.s3.amazonaws.com/{key}'
    __download_file_from_url(url, str(fpath))


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
                __defaults["progress_func"](dl, total)
        if not __defaults["silent"]:
            print()
            print("Done")


def compile_blob(blob_name, version=None, shaves=None, req_data=None, req_files=None, output_dir=None, url=None,
                  use_cache=True, compile_params=None, data_type=None, download_ir=False, zoo_type=None, dry=False):
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
    if zoo_type is None:
        zoo_type = __defaults["zoo_type"]

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
        'no_cache': not use_cache,
    }
    if dry:
        url_params["dry"] = True

    data = {
        "myriad_shaves": str(shaves),
        "myriad_params_advanced": ' '.join(compile_params),
        "data_type": data_type,
        "download_ir": download_ir,
        'zoo_type': zoo_type,
        **req_data,
    }

    if not dry:
        hash_obj = hashlib.sha256(json.dumps({**url_params, **data}).encode())
        for file_path in req_files.values():
            with open(file_path, 'rb') as f:
                hash_obj.update(f.read())
        req_hash = hash_obj.hexdigest()

        new_cache_config = {
            **cache_config,
            req_hash: str(blob_path),
        }

        if use_cache:
            cached_path = None
            if req_hash in cache_config:
                cached_path = cache_config[req_hash]

            if blob_path.exists():
                cached_path = str(blob_path)

            if cached_path is not None:
                if is_valid_blob(cached_path):
                    return cached_path
                else:
                    print("Cached blob is invalid, will download a new one from API.")

        cache_config_path.parent.mkdir(parents=True, exist_ok=True)
        with cache_config_path.open('w') as f:
            json.dump(new_cache_config, f)

        if not __defaults["silent"]:
            print("Downloading {}...".format(blob_path))

        try:
            if not download_ir:
                __download_from_s3_bucket("{}.blob".format(req_hash), blob_path)
                return blob_path
        except FileNotFoundError:
            pass

    files = {
        name: open(path, 'rb') for name, path in req_files.items()
    }

    response = requests.post(
        "{}/compile?{}".format(url, urllib.parse.urlencode(url_params)),
        data=data,
        files=files,
        stream=not dry,
    )
    if response.status_code == 400:
        try:
            print(json.dumps(response.json(), indent=4))
        except:
            print(response.text)
    response.raise_for_status()

    if dry:
        return response.json()

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
    try:
        return compile_blob(name, req_data=body, **kwargs)
    except Exception as ex:
        # backup conversion
        print("Conversion failed due to {}".format(ex))
        shaves = kwargs.get("shaves", __defaults["shaves"])
        version = kwargs.get("version", __defaults["version"])
        print("Trying to find backup... (model=\"{}\", shaves=\"{}\", version=\"{}\")".format(name, shaves, version))
        output_dir = kwargs.get("output_dir", __defaults["output_dir"])
        blob_name = Path("{}_openvino_{}_{}shave.blob".format(name, version, shaves))
        blob_path = output_dir / blob_name
        blob_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            response = requests.get("http://artifacts.luxonis.com/artifactory/blobconverter-backup/blobs/{}".format(blob_name.name))
            response.raise_for_status()
            print("Backup found, downloading...")
            __download_from_response(
                response,
                output_dir / blob_name
            )
            return output_dir / blob_name
        except Exception as ex2:
            print("Unable to fetch model from backup server due to: {}".format(ex2))
            raise



def from_caffe(proto, model, data_type=None, optimizer_params=None, proto_size=None, proto_sha256=None, model_size=None, model_sha256=None, **kwargs):
    if optimizer_params is None:
        optimizer_params = __defaults["optimizer_params"]
    if data_type is None:
        data_type = __defaults["data_type"]

    proto_name = get_filename(proto)
    model_name = get_filename(model)

    # print(f"CAFFE {proto_name} {model_name}")
    if not is_valid_name(proto_name) or not is_valid_name(model_name):
        raise ValueError("Input model files must not contain '.' or '=' characters!")

    files = {}
    builder = ConfigBuilder()\
        .task_type("detection")\
        .framework("caffe") \
        .model_optimizer_args(optimizer_params + [
            "--data_type={}".format(data_type),
            "--input_model=$dl_dir/{}/{}".format(data_type, model_name),
            "--input_proto=$dl_dir/{}/{}".format(data_type, proto_name),
        ])

    if str(proto).startswith("http"):
        builder = builder.with_file(name=get_filename(proto), url=proto, size=proto_size, sha256=proto_sha256)
    else:
        proto_path = Path(proto)
        builder = builder.with_file(name=proto_path.name, path=proto_path)
        files[proto_path.name] = proto_path

    if str(model).startswith("http"):
        files["config"] = builder.with_file(name=get_filename(model), url=model, size=model_size, sha256=model_sha256)
    else:
        model_path = Path(model)
        files["config"] = builder.with_file(name=model_path.name, path=model_path).build()
        files[model_path.name] = model_path

    return compile_blob(blob_name=Path(proto_name).stem, req_data={"name": Path(proto_name).stem}, req_files=files, data_type=data_type, **kwargs)


def from_onnx(model, data_type=None, optimizer_params=None, model_size=None, model_sha256=None, **kwargs):
    if optimizer_params is None:
        optimizer_params = __defaults["optimizer_params"]
    if data_type is None:
        data_type = __defaults["data_type"]
    files = {}
    model_name = get_filename(model)

    # print(f"ONNX {model_name}")
    if not is_valid_name(model_name):
        raise ValueError("Input model file must not contain '.' or '=' characters!")

    builder = ConfigBuilder()\
        .task_type("detection")\
        .framework("onnx")\
        .model_optimizer_args(optimizer_params + [
            "--data_type={}".format(data_type),
            "--input_model=$dl_dir/{}/{}".format(data_type, model_name),
        ])

    if str(model).startswith("http"):
        files["config"] = builder\
            .with_file(name=get_filename(model), url=model, size=model_size, sha256=model_sha256)\
            .build()
    else:
        files["config"] = builder\
            .with_file(name=model_name, path=Path(model))\
            .build()
        files[model_name] = Path(model)

    return compile_blob(blob_name=Path(model_name).stem, req_data={"name": Path(model_name).stem}, req_files=files, data_type=data_type, **kwargs)


def from_tf(frozen_pb, data_type=None, optimizer_params=None, frozen_pb_size=None, frozen_pb_sha256=None, **kwargs):
    if optimizer_params is None:
        optimizer_params = __defaults["optimizer_params"]
    if data_type is None:
        data_type = __defaults["data_type"]
    files = {}
    frozen_pb_name = get_filename(frozen_pb)

    # print(f"TF {frozen_pb_name}")
    if not is_valid_name(frozen_pb_name):
        raise ValueError("Input model file must not contain '.' or '=' characters!")

    builder = ConfigBuilder()\
        .task_type("detection")\
        .framework("tf")\
        .model_optimizer_args(optimizer_params + [
            "--data_type={}".format(data_type),
            "--input_model=$dl_dir/{}/{}".format(data_type, frozen_pb_name),
        ])

    if str(frozen_pb).startswith("http"):
        files["config"] = builder.with_file(name=get_filename(frozen_pb), url=frozen_pb, size=frozen_pb_size, sha256=frozen_pb_sha256).build()
    else:
        files["config"] = builder.with_file(name=frozen_pb_name, path=Path(frozen_pb)).build()
        files[frozen_pb_name] = Path(frozen_pb)

    return compile_blob(blob_name=Path(frozen_pb_name).stem, req_data={"name": Path(frozen_pb_name).stem}, req_files=files, data_type=data_type, **kwargs)


def from_openvino(xml, bin, xml_size=None, xml_sha256=None, bin_size=None, bin_sha256=None, **kwargs):
    files = {}
    builder = ConfigBuilder()\
        .task_type("detection")\
        .framework("dldt")
    xml_name = get_filename(xml)
    bin_name = get_filename(bin)

    # print(f"IR {xml_name} {bin_name}")
    if not is_valid_name(xml_name) or not is_valid_name(bin_name):
        raise ValueError("Input model files must not contain '.' or '=' characters!")

    if str(xml).startswith("http"):
        builder = builder.with_file(name=xml_name, url=xml, size=xml_size, sha256=xml_sha256)
    else:
        builder = builder.with_file(name=xml_name, path=Path(xml))
        files[xml_name] = Path(xml)

    if str(bin).startswith("http"):
        builder = builder.with_file(name=bin_name, url=bin, size=bin_size, sha256=bin_sha256)
    else:
        builder = builder.with_file(name=bin_name, path=Path(bin))
        files[bin_name] = Path(bin)

    files["config"] = builder.build()
    return compile_blob(blob_name=Path(xml_name).stem, req_data={"name": Path(xml_name).stem}, req_files=files, **kwargs)


def from_config(name, path, **kwargs):
    body = {
        "name": name,
        "use_zoo": "True",
    }
    files = {
        'config': path,
    }
    return compile_blob(blob_name=name, req_data=body, req_files=files, **kwargs)


def zoo_list(version=None, url=None, zoo_type='intel'):
    if url is None:
        url = __defaults["url"]
    if version is None:
        version = __defaults["version"]
    if zoo_type is None:
        zoo_type = __defaults["zoo_type"]

    url_params = {
        'version': version,
        'zoo_type': zoo_type
    }

    response = requests.get("{}/zoo_models?{}".format(url, urllib.parse.urlencode(url_params)))
    response.raise_for_status()
    return response.json()['available']



def __run_cli__():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-zn', '--zoo-name', help="Name of a model to download from OpenVINO Model Zoo")
    parser.add_argument('-zt', '--zoo-type', help="Type of the model zoo to use, available: \"intel\", \"depthai\" ")
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
    parser.add_argument('-v', '--version', choices=[Versions.v2021_2, Versions.v2021_3, Versions.v2021_4, Versions.v2022_1, Versions.v2022_3_RVC3], help=f"OpenVINO version to use for conversion. To export model for RVC3, you must set OpenVINO version to '{Versions.v2022_3_RVC3}'.")
    parser.add_argument('--optimizer-params', help="Additional params to use when converting a model to OpenVINO IR")
    parser.add_argument('--compile-params', help="Additional params to use when compiling a model to MyriadX blob")
    parser.add_argument('--converter-url', dest="url", help="URL to BlobConverter API endpoint used for conversion")
    parser.add_argument('--no-cache', dest="use_cache", action="store_false", help="Omit .cache directory and force new compilation of the blob")
    parser.add_argument('--dry', dest="dry", action="store_true", help="Instead of compiling the blob, return compilation commands (for manual conversion)")
    parser.add_argument('--zoo-list', action="store_true", help="List all models available in OpenVINO Model Zoo")
    parser.add_argument('--download-ir', action="store_true", help="Downloads OpenVINO IR files used to compile the blob. Result path points to a result ZIP archive")

    args = parser.parse_args()

    optimizer_params = ['--' + param.strip() for param in args.optimizer_params.split('--') if param] if args.optimizer_params else []

    common_args = {
        arg: getattr(args, arg)
        for arg in ["shaves", "data_type", "output_dir", "version", "url", "compile_params", "download_ir", "zoo_type", "use_cache", "dry"]
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
