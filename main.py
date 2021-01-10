import os
import subprocess
import traceback
import uuid
from pathlib import Path

from flask import Flask, request, jsonify, send_file, render_template
from werkzeug.utils import secure_filename

app = Flask(__name__, static_url_path='', static_folder='websrc/build/')

UPLOAD_FOLDER = Path('/tmp/blobconverter')
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

class EnvResolver:
    def __init__(self):
        version = request.args.get('version')
        if version == "2020.1" or version is None or version == "":
            self.base_path = Path("/opt/intel/openvino2020_1")
            self.cache_path = Path("/tmp/modeldownloader/2020_1")
        elif version == "2021.1":
            self.base_path = Path("/opt/intel/openvino")
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
        self.intermediate_compiler_path = self.base_path / Path("deployment_tools/model_optimizer/mo.py")
        self.model_downloader_path = self.base_path / Path("deployment_tools/open_model_zoo/tools/downloader/downloader.py")

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


def run_command(command):
    resolver = EnvResolver()
    print("Running command: {}".format(command))
    split_cmd = command.rstrip(' ').split(' ')
    try:
        proc = subprocess.Popen(split_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=resolver.env)
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


def request_myriad():
    resolver = EnvResolver()
    definition_file = request.files.get('definition', None)
    weights_file = request.files.get('weights', None)
    compiler_params = request.form.get('compiler_params', '')

    if definition_file is None:
        return "File named \"definition\" must be present in the request form", 400
    if weights_file is None:
        return "File named \"weights\" must be present in the request form", 400

    if Path(definition_file.filename).suffix != ".xml":
        return "Definitions file must have .xml extension", 400
    if Path(weights_file.filename).suffix != ".bin":
        return "Definitions file must have .bin extension", 400

    definitions_path = resolver.workdir / Path(secure_filename(definition_file.filename))
    weights_path = definitions_path.with_suffix('.bin')
    output_path = definitions_path.with_suffix('.blob')
    output_filename = Path(definition_file.filename).with_suffix('.blob').name

    definition_file.save(definitions_path)
    weights_file.save(weights_path)

    run_command(f"{resolver.compiler_path} -m {definitions_path} -o {output_path} {compiler_params}")
    return send_file(output_path, as_attachment=True, attachment_filename=output_filename)


def request_zoo():
    resolver = EnvResolver()
    model_name = request.form.get('model_name', '')
    model_downloader_params = request.form.get('model_downloader_params', '')
    command = f"{resolver.model_downloader_path} --name {model_name} --output_dir {resolver.workdir} --cache_dir {resolver.cache_path} {model_downloader_params}"
    run_command(command)
    if os.path.exists(f"{resolver.workdir}/public/{model_name}/{model_name}.caffemodel") or os.path.exists(f"{resolver.workdir}/public/{model_name}/{model_name}.tf"):
        intermediate_compiler_params = request.form.get('intermediate_compiler_params', '')
        command = f"{resolver.intermediate_compiler_path} --output_dir {resolver.workdir} --input_model {resolver.workdir}/public/{model_name}/{model_name}.caffemodel --input_proto {resolver.workdir}/public/{model_name}/{model_name}.prototxt {intermediate_compiler_params}"
        run_command(command)
        definitions_path = resolver.workdir
    else:
        definitions_path = f"{resolver.workdir}/intel/{model_name}/FP16"
    compiler_params = request.form.get('compiler_params', '')
    command = f"{resolver.compiler_path} -m {definitions_path}/{model_name}.xml -o {resolver.workdir}/model.blob {compiler_params}"
    run_command(command)
    return send_file(f"{resolver.workdir}/model.blob", as_attachment=True, attachment_filename=f"{model_name}.blob")


def request_model():
    resolver = EnvResolver()
    model_type = request.form.get('model_type', '')
    intermediate_compiler_params = request.form.get('intermediate_compiler_params', '')
    model_file = request.files.get('model', None)
    proto_file = request.files.get('proto', None)

    model_path = resolver.workdir / Path(secure_filename(model_file.filename))
    definitions_path = model_path.with_suffix('.xml')
    output_path = model_path.with_suffix('.blob')
    output_filename = model_path.with_suffix('.bin').name

    if model_type == "caffe":
        if model_file is None:
            return "File named \"model\" must be present in the request form", 400
        if proto_file is None:
            return "File named \"proto\" must be present in the request form", 400

        if Path(model_file.filename).suffix != ".caffemodel":
            return "Model file must have .caffemodel extension", 400
        if Path(proto_file.filename).suffix != ".prototxt":
            return "Definitions file must have .prototxt extension", 400

        proto_path = model_path.with_suffix('.prototxt')
        model_file.save(model_path)
        proto_file.save(proto_path)
        command = f"{resolver.intermediate_compiler_path} --output_dir {resolver.workdir} --input_model {model_path} --input_proto {proto_path} {intermediate_compiler_params}"
        run_command(command)
    elif model_type == "tf":
        if model_file is None:
            return "File named \"model\" must be present in the request form", 400

        if Path(model_file.filename).suffix != ".pb":
            return "Model file must have .pb extension", 400

        model_file.save(model_path)
        command = f"{resolver.intermediate_compiler_path} --output_dir {resolver.workdir} --framework tf --input_model {model_path} {intermediate_compiler_params}"
        run_command(command)
    else:
        return jsonify(error=f"Invalid model type: {model_type}, supported: tf, caffe")

    compiler_params = request.form.get('compiler_params', '')
    command = f"{resolver.compiler_path} -m {definitions_path} -o {output_path} {compiler_params}"
    run_command(command)
    return send_file(output_path, as_attachment=True, attachment_filename=output_filename)


@app.errorhandler(CommandFailed)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.route("/zoo_models", methods=['GET'])
def get_zoo_models():
    resolver = EnvResolver()
    _, stdout, _ = run_command(f"{resolver.model_downloader_path} --print_all")
    return jsonify(available=stdout.decode().split())


@app.route("/compile", methods=['POST'])
def compile():
    compile_type = request.form.get('compile_type', '')
    if compile_type == "myriad":
        return request_myriad()
    if compile_type == "model":
        return request_model()
    if compile_type == "zoo":
        return request_zoo()
    else:
        return f"Unknown compile type: {compile_type}", 400


@app.route('/')
def root():
    return app.send_static_file('index.html')


app.run(host='0.0.0.0', port=8080)
