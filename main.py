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

app = Flask(__name__, static_url_path='', static_folder='websrc/build/')

UPLOAD_FOLDER = Path('/tmp/blobconverter')
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

bucket = boto3.resource('s3', aws_access_key_id=os.getenv("AWS_ACCESS"), aws_secret_access_key=os.getenv("AWS_SECRET"))\
    .Bucket('blobconverter')


class EnvResolver:
    def __init__(self):
        self.version = request.args.get('version')
        if self.version == "2021.4" or self.version is None or self.version == "":
            self.base_path = Path("/opt/intel/openvino")
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
        elif self.version == "2020.3":
            self.base_path = Path("/opt/intel/openvino2020_3")
            self.cache_path = Path("/tmp/modeldownloader/2020_3")
            self.converter_path = Path(__file__).parent / Path("model_compiler/openvino_2020.3/converter.py")
            self.downloader_path = Path(__file__).parent / Path("model_compiler/openvino_2020.3/downloader.py")
            self.venv_path = Path(__file__).parent / Path("venvs/venv2020_3")
        elif self.version == "2020.2":
            self.base_path = Path("/opt/intel/openvino2020_2")
            self.cache_path = Path("/tmp/modeldownloader/2020_2")
            self.converter_path = Path(__file__).parent / Path("model_compiler/openvino_2020.2/converter.py")
            self.downloader_path = Path(__file__).parent / Path("model_compiler/openvino_2020.2/downloader.py")
            self.venv_path = Path(__file__).parent / Path("venvs/venv2020_2")
        elif self.version == "2020.1":
            self.base_path = Path("/opt/intel/openvino2020_1")
            self.cache_path = Path("/tmp/modeldownloader/2020_1")
            self.converter_path = Path(__file__).parent / Path("model_compiler/openvino_2020.1/converter.py")
            self.downloader_path = Path(__file__).parent / Path("model_compiler/openvino_2020.1/downloader.py")
            self.venv_path = Path(__file__).parent / Path("venvs/venv2020_1")
        elif self.version == "2019_R3.1":
            self.base_path = Path("/opt/intel/openvino2019_3")
            self.cache_path = Path("/tmp/modeldownloader/2019_3")
            self.converter_path = Path(__file__).parent / Path("model_compiler/openvino_2019.3/converter.py")
            self.downloader_path = Path(__file__).parent / Path("model_compiler/openvino_2019.3/downloader.py")
            self.venv_path = Path(__file__).parent / Path("venvs/venv2019_3")
        else:
            raise ValueError(f'Unknown version: "{self.version}", available: "2021.4", "2021.3", "2021.2", "2021.1", "2020.4", "2020.3", "2020.2", "2020.1", "2019.R3"')

        self.workdir = UPLOAD_FOLDER / Path(uuid.uuid4().hex)
        self.workdir.mkdir(parents=True, exist_ok=True)
        self.cache_path.mkdir(parents=True, exist_ok=True)

        self.compiler_path = self.base_path / Path("deployment_tools/inference_engine/lib/intel64/myriad_compile")

        self.model_zoo_type = request.values.get('zoo_type', "intel")
        if self.model_zoo_type == "intel":
            self.model_zoo_path = self.base_path / Path("deployment_tools/open_model_zoo/models")
        elif self.model_zoo_type == "depthai":
            self.model_zoo_path = Path(__file__).parent / Path("depthai-model-zoo/models")
        else:
            raise ValueError(f'Unknown zoo name: "{self.model_zoo_type}", available: "intel", "depthai"')

        self.env = os.environ.copy()
        self.env['InferenceEngine_DIR'] = str(self.base_path / Path("deployment_tools/inference_engine/share"))
        self.env['INTEL_OPENVINO_DIR'] = str(self.base_path)
        self.env['OpenCV_DIR'] = str(self.base_path / Path("opencv/cmake"))
        self.env['LD_LIBRARY_PATH'] = f"{self.base_path}/opencv/lib:{self.base_path}/deployment_tools/ngraph/lib:/opt/intel/opencl:{self.base_path}/deployment_tools/inference_engine/external/hddl/lib:{self.base_path}/deployment_tools/inference_engine/external/gna/lib:{self.base_path}/deployment_tools/inference_engine/external/mkltiny_lnx/lib:{self.base_path}/deployment_tools/inference_engine/external/tbb/lib:{self.base_path}/deployment_tools/inference_engine/lib/intel64:"
        self.env['HDDL_INSTALL_DIR'] = str(self.base_path / Path("deployment_tools/inference_engine/external/hddl"))
        self.env['INTEL_CVSDK_DIR'] = str(self.base_path)
        self.env['INSTALLDIR'] = str(self.base_path)
        self.env['PYTHONPATH'] = f"{self.base_path}/python/python3.6:{self.base_path}/python/python3:{self.base_path}/deployment_tools/open_model_zoo/tools/accuracy_checker:{self.base_path}/deployment_tools/model_optimizer"
        self.env['PATH'] = f"{self.venv_path.absolute()}/bin:{self.base_path}/deployment_tools/model_optimizer:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
        self.env['VIRTUAL_ENV'] = str(self.venv_path.absolute())

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

    with open(config_path, "w", encoding='utf8') as f:
        yaml.dump(config, f , default_flow_style=False, allow_unicode=True)

    return config


def prepare_compile_config(shaves, env):
    if env.version.startswith('2021'):
        config_file_content = {
            'MYRIAD_NUMBER_OF_SHAVES': shaves,
            'MYRIAD_NUMBER_OF_CMX_SLICES': shaves,
            'MYRIAD_THROUGHPUT_STREAMS': 1
        }
    else:
        config_file_content = {
            'VPU_MYRIAD_PLATFORM': 'VPU_MYRIAD_2480',
            'VPU_NUMBER_OF_SHAVES': shaves,
            'VPU_NUMBER_OF_CMX_SLICES': shaves,
            'VPU_MYRIAD_THROUGHPUT_STREAMS': 1
        }
    config_file_path = env.workdir / "myriad_compile_config.txt"
    with open(config_file_path, "w") as f:
        f.writelines(
            [f"{key} {config_file_content[key]}\r\n" for key in config_file_content.keys()]
        )

    return config_file_path


def fetch_from_zoo(env, name):
    return next(env.model_zoo_path.rglob(f'**/{name}/model.yml'), None)


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
            f"{env.executable} {env.downloader_path} --precisions {data_type} --output_dir {env.workdir} --cache_dir {env.cache_path} --num_attempts 5 --name {name} --model_root {env.workdir}"
        )
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
    commands.append(f"{env.compiler_path} -m {xml_path} -o {out_path} -c {compile_config_path} {myriad_params_advanced}")

    hash_obj = hashlib.sha256(json.dumps({**dict(request.args), **dict(request.values)}).encode())
    if config_file is not None:
        hash_obj.update(raw_config.encode())
    for file_path in list(file_paths.values()):
        with open(file_path, 'rb') as f:
            hash_obj.update(f.read())
    req_hash = hash_obj.hexdigest()

    if "dry" in request.args:
        return jsonify(commands)

    data = None
    try:
        if not no_cache or not download_ir:
            data = bucket.Object("{}.blob".format(req_hash)).get()['Body'].read()
            with out_path.open("wb") as f:
                f.write(data)
    except botocore.exceptions.ClientError as ex:
        if ex.response['Error']['Code'] != 'NoSuchKey':
            raise ex
    if data is None:
        for command in commands:
            env.run_command(command)

    major, minor = env.version.replace('_R3', '').split('.')
    with open(out_path, 'rb+') as f:
        f.seek(60)
        f.write(int(major).to_bytes(4, byteorder="little"))
        f.write(int(minor).to_bytes(4, byteorder="little"))
        
        if not download_ir:
            f.seek(0)
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
    response.status_code = error.status_code
    return response


@app.route("/zoo_models", methods=['GET'])
def get_zoo_models():
    env = EnvResolver()
    _, stdout, _ = env.run_command(f"{env.executable} {env.downloader_path} --model_root {env.model_zoo_path} --print_all")
    return jsonify(available=stdout.decode().split())


@app.route("/update", methods=['GET'])
def update():
    subprocess.check_call(["/bin/bash", "/app/docker_scheduled.sh"])
    return jsonify(status="Updated")


@app.route('/')
def root():
    return app.send_static_file('index.html')
