import os
import subprocess
import traceback
import uuid
from pathlib import Path
import sys
from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename
import yaml
import hashlib

app = Flask(__name__, static_url_path='', static_folder='websrc/build/')

UPLOAD_FOLDER = Path('/tmp/blobconverter')
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

class EnvResolver:
    def __init__(self):
        version = request.args.get('version')
        if version == "2020.1" or version is None or version == "":
            self.base_path = Path("/opt/intel/openvino")
            self.cache_path = Path("/tmp/modeldownloader/2020_1")
        elif version == "2021.1":
            self.base_path = Path("/opt/intel/openvino2021_1")
            self.cache_path = Path("/tmp/modeldownloader/2021_1")
        elif version == "2020.4":
            self.base_path = Path("/opt/intel/openvino2020_4")
            self.cache_path = Path("/tmp/modeldownloader/2020_4")
        elif version == "2020.3":
            self.base_path = Path("/opt/intel/openvino2020_3")
            self.cache_path = Path("/tmp/modeldownloader/2020_3")
        elif version == "2020.2":
            self.base_path = Path("/opt/intel/openvino2020_2")
            self.cache_path = Path("/tmp/modeldownloader/2020_2")
        elif version == "2019.R3":
            self.base_path = Path("/opt/intel/openvino2019_3")
            self.cache_path = Path("/tmp/modeldownloader/2019_3")
        else:
            raise ValueError(f'Unknown version: "{version}", available: "2021.1", "2020.4", "2020.3", "2020.2", "2020.1", "2019.R3"')

        self.workdir = UPLOAD_FOLDER / Path(uuid.uuid4().hex)
        self.workdir.mkdir(parents=True, exist_ok=True)
        self.cache_path.mkdir(parents=True, exist_ok=True)

        self.compiler_path = self.base_path / Path("deployment_tools/inference_engine/lib/intel64/myriad_compile")
        self.intermediate_compiler_path = Path(__file__).parent / Path("downloader/converter.py")  # TODO remove
        self.converter_path = Path(__file__).parent / Path("downloader/converter.py")
        self.model_downloader_path = Path(__file__).parent / Path("downloader/downloader.py")  # TODO remove
        self.downloader_path = Path(__file__).parent / Path("downloader/downloader.py")

        self.env = os.environ.copy()
        self.env['InferenceEngine_DIR'] = str(self.base_path / Path("deployment_tools/inference_engine/share"))
        self.env['INTEL_OPENVINO_DIR'] = str(self.base_path)
        self.env['OpenCV_DIR'] = str(self.base_path / Path("opencv/cmake"))
        self.env['LD_LIBRARY_PATH'] = f"{self.base_path}/opencv/lib:{self.base_path}/deployment_tools/ngraph/lib:/opt/intel/opencl:{self.base_path}/deployment_tools/inference_engine/external/hddl/lib:{self.base_path}/deployment_tools/inference_engine/external/gna/lib:{self.base_path}/deployment_tools/inference_engine/external/mkltiny_lnx/lib:{self.base_path}/deployment_tools/inference_engine/external/tbb/lib:{self.base_path}/deployment_tools/inference_engine/lib/intel64:"
        self.env['HDDL_INSTALL_DIR'] = str(self.base_path / Path("deployment_tools/inference_engine/external/hddl"))
        self.env['INTEL_CVSDK_DIR'] = str(self.base_path)
        self.env['INSTALLDIR'] = str(self.base_path)
        self.env['PYTHONPATH'] = f"{self.base_path}/python/python3.6:{self.base_path}/python/python3:{self.base_path}/deployment_tools/open_model_zoo/tools/accuracy_checker:{self.base_path}/deployment_tools/model_optimizer"
        self.env['PATH'] = f"{self.base_path}/deployment_tools/model_optimizer:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

    def run_command(self, command):
        print("Running command: {}".format(command))
        split_cmd = command.rstrip(' ').split(' ')
        try:
            proc = subprocess.Popen(split_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=self.env)
            stdout, stderr = proc.communicate()
            print("Command returned exit code: {}".format(proc.returncode))
            if proc.returncode != 0:
                raise CommandFailed(
                    message=f"Command failed with exit code {proc.returncode}, command: {command}",
                    payload=dict(
                        stderr=stderr.decode(),
                        stdout=stdout.decode(),
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
    status_code = 500

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

def parse_config(config_path, name, env):
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    if "description" not in config:
        config["description"] = f"Configuration file generated for {name} model"

    if "license" not in config:
        config["license"] = f"Unknown"

    if "files" not in config:
        raise BadRequest("\"files\" property is missing in model config file")

    if "compile_params" not in config:
        raise BadRequest("\"compile_params\" property is missing in model config file")

    for file in config["files"]:
        if "source" not in file:
            raise BadRequest("Each file needs to have \"source\" param")
        if file["source"]["$type"] == "http":
            local_path = file["source"]["url"].replace("$REQUEST", str((env.workdir / name).absolute()))
            file["source"]["url"] = "file://" + local_path
        if "size" not in file:
            if file["source"]["$type"] != "http" or not file["source"]["url"].startswith("file://"):
                raise BadRequest("You need to supply \"size\" parameter for file when using a remote source")
            file["size"] = Path(local_path).stat().st_size
        if "sha256" not in file:
            if file["source"]["$type"] != "http" or not file["source"]["url"].startswith("file://"):
                raise BadRequest("You need to supply \"sha256\" parameter for file when using a remote source")
            file["sha256"] = sha256sum(local_path)

    with open(config_path, "w", encoding='utf8') as f:
        yaml.dump(config, f , default_flow_style=False, allow_unicode=True)

    return config

@app.route("/compile", methods=['POST'])
def compile():
    env = EnvResolver()
    name = request.form.get('name', '')
    config_file = request.files.get("config", None)
    if config_file is None:
        return "File named \"config\" must be present in the request form", 400
    config_path = env.workdir / name / "model.yml"
    config_path.parent.mkdir(parents=True)
    config_file.save(config_path)

    file_paths = {}
    for form_name, file in request.files.items():
        if form_name == "config":
            continue
        path = env.workdir / name / secure_filename(file.filename)
        file_paths[form_name] = path
        file.save(path)

    config = parse_config(config_path, name, env)

    env.run_command(f"{sys.executable} {env.downloader_path} --output_dir {env.workdir} --cache_dir {env.cache_path} --num_attempts 5 --name {name} --model_root {env.workdir}")
    env.run_command(f"{sys.executable} {env.converter_path} --precisions FP16 --output_dir {env.workdir} --download_dir {env.workdir} --name {name} --model_root {env.workdir}")
    xml_path = env.workdir / name / "FP16" / (name + ".xml")
    out_path = xml_path.with_suffix('.blob')
    env.run_command(f"{env.compiler_path} -m {xml_path} -o {out_path} {config['compile_params']}")
    return send_file(out_path, as_attachment=True, attachment_filename=out_path.name)


@app.errorhandler(CommandFailed)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.route("/zoo_models", methods=['GET'])
def get_zoo_models():
    env = EnvResolver()
    _, stdout, _ = env.run_command(f"{env.model_downloader_path} --print_all")
    return jsonify(available=stdout.decode().split())


@app.route('/')
def root():
    return app.send_static_file('index.html')


app.run(host='0.0.0.0', port=8080)
