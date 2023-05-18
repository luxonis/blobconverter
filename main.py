import json
import os
import shutil
import ssl
import subprocess

import traceback
import uuid
import zipfile
from pathlib import Path
from flask import Flask, request, jsonify, send_file, after_this_request, make_response
from werkzeug.utils import secure_filename
import yaml
import hashlib
import boto3
import botocore
import sentry_sdk
import requests


SENTRY_TOKEN = os.getenv("SENTRY_TOKEN")
LOG_URL = os.getenv("LOG_URL")

if SENTRY_TOKEN is not None:
    sentry_sdk.init(
        dsn=SENTRY_TOKEN
    )

app = Flask(__name__, static_url_path='', static_folder='websrc/build/')

UPLOAD_FOLDER = Path('/tmp/blobconverter')
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

AWS_ACCESS = os.getenv("AWS_ACCESS")
AWS_SECRET = os.getenv("AWS_SECRET")
# ugly fix to prevent caching
AWS_CACHE = (AWS_ACCESS is not None and AWS_ACCESS != "") and (AWS_SECRET is not None and AWS_SECRET != "")
print(AWS_CACHE)

if AWS_CACHE:
    bucket = boto3.resource('s3', aws_access_key_id=AWS_ACCESS, aws_secret_access_key=AWS_SECRET)\
        .Bucket('blobconverter')


class EnvResolver:
    def __init__(self):
        self.version = request.args.get('version')
        self.compiler_path = None
        if self.version == "2022.1" or self.version is None or self.version == "":
            self.base_path = Path("/opt/intel/openvino2022_1")
            self.cache_path = Path("/tmp/modeldownloader/2022_1")
            self.version = "2022.1"
            self.converter_path = Path(__file__).parent / Path("model_compiler/openvino_2022.1/converter.py")
            self.downloader_path = Path(__file__).parent / Path("model_compiler/openvino_2022.1/downloader.py")
            self.venv_path = Path(__file__).parent / Path("venvs/venv2022_1")
            self.compiler_path = self.base_path / Path("tools/compile_tool/compile_tool")
        elif self.version == "2022.3_RVC3":
            self.base_path = Path("/opt/intel/openvino2022_3_RVC3")
            self.cache_path = Path("/tmp/modeldownloader/2022_3_RVC3")
            self.version = "2022.3_RVC3"
            self.converter_path = Path(__file__).parent / Path("model_compiler/openvino_2022.3_RVC3/converter.py")
            self.downloader_path = Path(__file__).parent / Path("model_compiler/openvino_2022.3_RVC3/downloader.py")
            self.venv_path = Path(__file__).parent / Path("venvs/venv2022_3_RVC3")
            self.compiler_path = self.base_path / Path("tools/compile_tool/compile_tool")
        elif self.version == "2021.4":
            self.base_path = Path("/opt/intel/openvino2021_4")
            self.cache_path = Path("/tmp/modeldownloader/2021_4")
            self.version = "2021.4"
            self.converter_path = Path(__file__).parent / Path("model_compiler/openvino_2021.4/converter.py")
            self.downloader_path = Path(__file__).parent / Path("model_compiler/openvino_2021.4/downloader.py")
            self.venv_path = Path(__file__).parent / Path("venvs/venv2021_4")
        elif self.version == "2021.3":
            self.base_path = Path("/opt/intel/openvino2021_3")
            self.cache_path = Path("/tmp/modeldownloader/2021_3")
            self.converter_path = Path(__file__).parent / Path("model_compiler/openvino_2021.3/converter.py")
            self.downloader_path = Path(__file__).parent / Path("model_compiler/openvino_2021.3/downloader.py")
            self.venv_path = Path(__file__).parent / Path("venvs/venv2021_3")
        elif self.version == "2021.2":
            self.base_path = Path("/opt/intel/openvino2021_2")
            self.cache_path = Path("/tmp/modeldownloader/2021_2")
            self.converter_path = Path(__file__).parent / Path("model_compiler/openvino_2021.2/converter.py")
            self.downloader_path = Path(__file__).parent / Path("model_compiler/openvino_2021.2/downloader.py")
            self.venv_path = Path(__file__).parent / Path("venvs/venv2021_2")
        elif self.version == "2021.1":
            self.base_path = Path("/opt/intel/openvino2021_1")
            self.cache_path = Path("/tmp/modeldownloader/2021_1")
            self.converter_path = Path(__file__).parent / Path("model_compiler/openvino_2021.1/converter.py")
            self.downloader_path = Path(__file__).parent / Path("model_compiler/openvino_2021.1/downloader.py")
            self.venv_path = Path(__file__).parent / Path("venvs/venv2021_1")
        elif self.version == "2020.4":
            self.base_path = Path("/opt/intel/openvino2020_4")
            self.cache_path = Path("/tmp/modeldownloader/2020_4")
            self.converter_path = Path(__file__).parent / Path("model_compiler/openvino_2020.4/converter.py")
            self.downloader_path = Path(__file__).parent / Path("model_compiler/openvino_2020.4/downloader.py")
            self.venv_path = Path(__file__).parent / Path("venvs/venv2020_4")
        else:
            raise ValueError(f'Unknown version: "{self.version}", available: "2022.3_RVC3", "2022.1", "2021.4", "2021.3", "2021.2", "2021.1", "2020.4"')


        self.workdir = UPLOAD_FOLDER / Path(uuid.uuid4().hex)
        self.workdir.mkdir(parents=True, exist_ok=True)
        self.cache_path.mkdir(parents=True, exist_ok=True)
        (self.cache_path / "FP16").mkdir(parents=True, exist_ok=True)
        (self.cache_path / "FP16-INT8").mkdir(parents=True, exist_ok=True)

        if self.compiler_path is None:
            self.compiler_path = self.base_path / Path("deployment_tools/inference_engine/lib/intel64/myriad_compile")

        self.model_zoo_type = request.values.get('zoo_type', "intel")
        if self.model_zoo_type == "intel":
            if self.version in ["2022.1", "2022.3_RVC3"]:
                self.model_zoo_path = Path("/app/models/2022_1")
            else:
                self.model_zoo_path = self.base_path / Path("deployment_tools/open_model_zoo/models")
        elif self.model_zoo_type == "depthai":
            self.model_zoo_path = Path(__file__).parent / Path("git/depthai-model-zoo/models")
        else:
            raise ValueError(f'Unknown zoo name: "{self.model_zoo_type}", available: "intel", "depthai"')

        self.env = os.environ.copy()
        
        self.env['INTEL_OPENVINO_DIR'] = str(self.base_path)
        self.env['OpenCV_DIR'] = str(self.base_path / Path("opencv/cmake"))
       
        self.env['INTEL_CVSDK_DIR'] = str(self.base_path)
        self.env['INSTALLDIR'] = str(self.base_path)
        self.env['VIRTUAL_ENV'] = str(self.venv_path.absolute())

        if self.version in ["2022.1", "2022.3_RVC3"]:
            self.env['InferenceEngine_DIR'] = str(self.base_path / Path("runtime/cmake"))
            self.env['LD_LIBRARY_PATH'] = f"{self.base_path}/tools/compile_tool:{self.base_path}/extras/opencv/lib:{self.base_path}/deployment_tools/ngraph/lib:/opt/intel/opencl:{self.base_path}/runtime/3rdparty/hddl/lib:{self.base_path}/deployment_tools/inference_engine/external/gna/lib:{self.base_path}/deployment_tools/inference_engine/external/mkltiny_lnx/lib:{self.base_path}/runtime/3rdparty/tbb/lib:{self.base_path}/runtime/lib/intel64:"
            self.env['HDDL_INSTALL_DIR'] = str(self.base_path / Path("runtime/3rdparty/hddl"))
            self.env['PYTHONPATH'] = f"{self.base_path}/python/python3.8:{self.base_path}/python/python3:{self.base_path}/deployment_tools/open_model_zoo/tools/accuracy_checker:{self.base_path}/extras/opencv/python"
            self.env['PATH'] = f"{self.venv_path.absolute()}/bin:{self.base_path}/deployment_tools/model_optimizer:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/{self.venv_path.absolute()}/lib/python3.8/site-packages/openvino/libs"
        else:
            self.env['InferenceEngine_DIR'] = str(self.base_path / Path("deployment_tools/inference_engine/share"))
            self.env['LD_LIBRARY_PATH'] = f"{self.base_path}/opencv/lib:{self.base_path}/deployment_tools/ngraph/lib:/opt/intel/opencl:{self.base_path}/deployment_tools/inference_engine/external/hddl/lib:{self.base_path}/deployment_tools/inference_engine/external/gna/lib:{self.base_path}/deployment_tools/inference_engine/external/mkltiny_lnx/lib:{self.base_path}/deployment_tools/inference_engine/external/tbb/lib:{self.base_path}/deployment_tools/inference_engine/lib/intel64:"
            self.env['HDDL_INSTALL_DIR'] = str(self.base_path / Path("deployment_tools/inference_engine/external/hddl"))
            self.env['PYTHONPATH'] = f"{self.base_path}/python/python3.6:{self.base_path}/python/python3:{self.base_path}/deployment_tools/open_model_zoo/tools/accuracy_checker:{self.base_path}/deployment_tools/model_optimizer"
            self.env['PATH'] = f"{self.venv_path.absolute()}/bin:{self.base_path}/deployment_tools/model_optimizer:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
            

    @property
    def executable(self):
        return str((self.venv_path / "bin" / "python").absolute())

    def run_command(self, command):
        print("Running command: {}".format(command))
        split_cmd = command.rstrip(' ').split(' ')
        try:
            proc = subprocess.Popen(split_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=self.env)
            stdout, stderr = proc.communicate()
            print("Command returned exit code: {}".format(proc.returncode))
            if proc.returncode != 0:
                filtered_stdout = "\n".join(filter(
                    lambda line: "[myriad_compile] usb_find_device_with_bcd:266\tLibrary has not been initialized when loaded" not in line,
                    stdout.decode().split("\n")
                ))
                print(filtered_stdout.split("\n"))
                raise CommandFailed(
                    message=f"Command failed with exit code {proc.returncode}, command: {command}",
                    payload=dict(
                        stderr=stderr.decode(),
                        stdout=filtered_stdout,
                        exit_code=proc.returncode
                    )
                )
            return proc, stdout, stderr
        except CommandFailed:
            raise
        except Exception:
            raise CommandFailed(
                message=f"Command was unable to execute, command: {command}",
                payload=dict(
                    stderr=traceback.format_exc(),
                    stdout="",
                    exit_code=-1
                )
            )


def sha256sum(filename):
    h  = hashlib.sha256()
    b  = bytearray(128*1024)
    mv = memoryview(b)
    with open(filename, 'rb', buffering=0) as f:
        for n in iter(lambda : f.readinto(mv), 0):
            h.update(mv[:n])
    return h.hexdigest()

def sha384sum(filename):
    h  = hashlib.sha384()
    b  = bytearray(128*1024)
    mv = memoryview(b)
    with open(filename, 'rb', buffering=0) as f:
        for n in iter(lambda : f.readinto(mv), 0):
            h.update(mv[:n])
    return h.hexdigest()


class CommandFailed(Exception):
    status_code = 400

    def __init__(self, message, payload=None):
        Exception.__init__(self)
        self.message = message
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv


class BadRequest(CommandFailed):
    status_code = 400


def parse_config(config_path, name, data_type, env):
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    if "description" not in config:
        config["description"] = f"Configuration file generated for {name} model"

    if "license" not in config:
        config["license"] = f"Unknown"

    if "files" not in config:
        raise BadRequest("\"files\" property is missing in model config file")

    for file in config["files"]:
        if "source" not in file:
            raise BadRequest("Each file needs to have \"source\" param")
        if "$type" in file["source"]:
            if file["source"]["$type"] == "http" and "$REQUEST" in file["source"]["url"]:
                local_path = file["source"]["url"].replace("$REQUEST", str((env.workdir / name / data_type).absolute()))
                file["source"]["url"] = "file://" + local_path
            if "size" not in file:
                if not file["source"]["url"].startswith("file://"):
                    raise BadRequest("You need to supply \"size\" parameter for file when using a remote source")
                file["size"] = Path(local_path).stat().st_size
            if "sha256" not in file:
                if not file["source"]["url"].startswith("file://"):
                    raise BadRequest("You need to supply \"sha256\" parameter for file when using a remote source")
                file["sha256"] = sha256sum(local_path)
            if "sha384" not in file:
                if not file["source"]["url"].startswith("file://"):
                    raise BadRequest("You need to supply \"sha384\" parameter for file when using a remote source")
                file["sha384"] = sha384sum(local_path)
            if "checksum" not in file:
                file["checksum"] = file["sha384"]

    with open(config_path, "w", encoding='utf8') as f:
        yaml.dump(config, f , default_flow_style=False, allow_unicode=True)

    return config


def prepare_compile_config(shaves, env):
    if env.version.endswith('RVC3'):
        config_file_content = {
            'PERFORMANCE_HINT': 'THROUGHPUT'
        }
    elif env.version.startswith('2022'):
        config_file_content = {
            'MYRIAD_NUMBER_OF_SHAVES': shaves,
            'MYRIAD_NUMBER_OF_CMX_SLICES': shaves,
            'MYRIAD_THROUGHPUT_STREAMS': 1,
            'MYRIAD_ENABLE_MX_BOOT':'NO'
        }
    elif env.version.startswith('2020'):
        config_file_content = {
            'VPU_MYRIAD_PLATFORM': 'VPU_MYRIAD_2480',
            'VPU_NUMBER_OF_SHAVES': shaves,
            'VPU_NUMBER_OF_CMX_SLICES': shaves,
            'VPU_MYRIAD_THROUGHPUT_STREAMS': 1
        }
    else:
        config_file_content = {
            'MYRIAD_NUMBER_OF_SHAVES': shaves,
            'MYRIAD_NUMBER_OF_CMX_SLICES': shaves,
            'MYRIAD_THROUGHPUT_STREAMS': 1
        }
    config_file_path = env.workdir / "myriad_compile_config.txt"
    with open(config_file_path, "w") as f:
        f.writelines(
            [f"{key} {config_file_content[key]}\n" for key in config_file_content.keys()]
        )

    return config_file_path


def fetch_from_zoo(env, name):
    return next(env.model_zoo_path.rglob(f'**/{name}/model.yml'), None)

def format_model_list(models_available_fp16, models_available_int8, models_unavailable):
    output = {
        "version": "2", 
        "available" : [], 
        "unavailable" : []
    }

    for model in models_available_fp16:
        entry = {
            "name" : model,
            "data_types": ["FP16"]
        }
        if model in models_available_int8:
            entry["data_types"].append("FP16-INT8")
            models_available_int8.remove(model)

        output["available"].append(entry)
    
    for model in models_available_int8:
        entry = {
            "name" : model,
            "data_types": ["FP16-INT8"]
        }
        output["available"].append(entry)
    
    return output


@app.route("/compile", methods=['GET', 'POST'])
def compile():
    env = EnvResolver()
    name = request.values.get('name', '')
    if len(name) == 0:
        return "Parameter \"name\" is empty!", 400
    myriad_shaves = int(request.values.get('myriad_shaves', '6'))
    myriad_params_advanced = request.values.get('myriad_params_advanced', '-ip U8')
    config_path = env.workdir / name / "model.yml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_file = request.files.get("config", None)
    use_zoo = request.values.get('use_zoo', False)
    data_type = request.values.get('data_type', "FP16")
    download_ir = request.values.get('download_ir', "false").lower() == "true"
    no_cache = request.args.get('no_cache', "false") == "true"
    quantization_domain = request.args.get('quantization_domain', "ABC")

    print(f"GOT QUANTIZATION DOMAIN: {quantization_domain}")

    if (LOG_URL is not None):
        content = f"{name}, Params: {myriad_params_advanced}"
        requests.post(LOG_URL, json={"text": content })

    if config_file is None:
        if use_zoo:
            zoo_path = fetch_from_zoo(env, name)
            if zoo_path is None:
                return "Model {} not found in model zoo".format(name), 400
            with zoo_path.open() as in_f, config_path.open("w") as out_f:
                out_f.write(in_f.read())
        else:
            return "File named \"config\" must be present in the request form", 400
    else:
        config_file.save(config_path)
        with open(config_path) as f:
            raw_config = f.read()

    file_paths = {}
    for form_name, file in request.files.items():
        if form_name == "config":
            continue
        path = env.workdir / name / data_type / secure_filename(file.filename)
        path.parent.mkdir(parents=True, exist_ok=True)
        file_paths[form_name] = path
        file.save(path)

    config = parse_config(config_path, name, data_type, env)
    compile_config_path = prepare_compile_config(myriad_shaves, env)
    commands = []
    xml_path = env.workdir / name / data_type / (name + ".xml")
    if len(file_paths) == 0:
        commands.append(
            f"{env.executable} {env.downloader_path} --precisions {data_type} --output_dir {env.workdir} --cache_dir {env.cache_path / data_type} --num_attempts 5 --name {name} --model_root {env.workdir}"
        )
        print(commands)
    if use_zoo:
        preconvert_script = next(env.model_zoo_path.rglob(f"**/{name}/pre-convert.py"), None)
        if preconvert_script is not None:
            commands.append(
                f"{env.executable} {preconvert_script} {env.workdir / name} {env.workdir / name}"
            )

    if config["framework"] != "dldt":
        commands.append(
            f"{env.executable} {env.converter_path} --precisions {data_type} --output_dir {env.workdir} --download_dir {env.workdir} --name {name} --model_root {env.workdir}"
        )

    out_path = xml_path.with_suffix('.blob')
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if env.version == "2022.3_RVC3":
        commands.append(f"{env.compiler_path} -m {xml_path} -o {out_path} -d VPUX.3400 {myriad_params_advanced}")

    elif env.version == "2022.1":
        commands.append(f"{env.compiler_path} -m {xml_path} -o {out_path} -c {compile_config_path} -d MYRIAD {myriad_params_advanced}")
    else:
        commands.append(f"{env.compiler_path} -m {xml_path} -o {out_path} -c {compile_config_path} {myriad_params_advanced}")
    hash_obj = hashlib.sha256(json.dumps({**dict(request.args), **dict(request.values)}).encode())
    if config_file is not None:
        hash_obj.update(raw_config.encode())
    for file_path in list(file_paths.values()):
        with open(file_path, 'rb') as f:
            hash_obj.update(f.read())
    req_hash = hash_obj.hexdigest()

    if request.args.get("dry", "false") == "true":
        return jsonify(commands)

    data = None
    model_from_cache = False
    if AWS_CACHE:
        try:
            if not no_cache or not download_ir:
                print(f"Trying to get blob {req_hash} from cache...")
                data = bucket.Object("{}.blob".format(req_hash)).get()['Body'].read()
                with out_path.open("wb") as f:
                    f.write(data)
                print(f"Data {req_hash} found in cache...")
                
        except botocore.exceptions.ClientError as ex:
            print(f"Data {req_hash} not found in cache...")
            if ex.response['Error']['Code'] != 'NoSuchKey':
                raise ex
    if data is None:
        for command in commands:
            env.run_command(command)
    else:
        model_from_cache = True

    major, minor = env.version.replace('_R3', '').replace('_RVC3', '').split('.')


    if not env.version in ["2022.3_RVC3"]:
        with open(out_path, 'rb+') as f:
            f.seek(60)
            f.write(int(major).to_bytes(4, byteorder="little"))
            f.write(int(minor).to_bytes(4, byteorder="little"))

            if AWS_CACHE:
                if not download_ir and not model_from_cache:
                    f.seek(0)
                    print(f"Uploading final blob {req_hash} to the cache...")
                    bucket.put_object(Body=f.read(), Key='{}.blob'.format(req_hash))

    if download_ir:
        zipf = zipfile.ZipFile(out_path.with_suffix('.zip'), 'w', zipfile.ZIP_DEFLATED)
        zipf.write(xml_path, xml_path.name)
        zipf.write(xml_path.with_suffix('.bin'), xml_path.with_suffix('.bin').name)
        zipf.write(out_path, out_path.name)
        zipf.close()
        out_path = out_path.with_suffix('.zip')

    @after_this_request
    def remove_dir(response):
        shutil.rmtree(env.workdir, ignore_errors=True)
        return response

    response = make_response(send_file(out_path, as_attachment=True, attachment_filename=out_path.name))
    response.headers['X-HASH'] = req_hash
    return response


@app.errorhandler(CommandFailed)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    sentry_sdk.capture_exception(error)
    response.status_code = error.status_code
    return response


@app.route("/zoo_models", methods=['GET'])
def get_zoo_models():
    # TODO: Add RVC3 models for Intel zoo
    env = EnvResolver()
    if env.version == "2022.1" and env.model_zoo_type == "intel":
        with open('./models/openvino_2022_1.json', 'r') as file:
            data = json.loads(file.read())  # format to new style for now
            return format_model_list(data["available"], [], [])
    elif env.version == "2022.3_RVC3" and env.model_zoo_type == "depthai":
        with open('./models/depthai_2022_1_RVC3_new.json', 'r') as file:
            return file.read()
    elif env.version == "2022.3_RVC3" and env.model_zoo_type == "intel":
        with open('./models/intel_2022_1_RVC3_new.json', 'r') as file:
            return file.read()  # proper format
    _, stdout, _ = env.run_command(f"{env.executable} {env.downloader_path} --model_root {env.model_zoo_path} --print_all")
    
    return format_model_list(stdout.decode().split(), [], [])


@app.route("/update", methods=['GET'])
def update():
    subprocess.check_call(["/bin/bash", "/app/docker_scheduled.sh"])
    return jsonify(status="Updated")


@app.route('/')
def root():
    return app.send_static_file('index.html')
