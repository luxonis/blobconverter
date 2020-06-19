import os
import subprocess
import traceback
import uuid
from pathlib import Path

from flask import Flask, request, jsonify, send_file, render_template
from werkzeug.utils import secure_filename

app = Flask(__name__)

compiler_path = "/opt/intel/openvino/deployment_tools/inference_engine/lib/intel64/myriad_compile"
intermediate_compiler_path = "/opt/intel/openvino/deployment_tools/model_optimizer/mo.py"
model_downloader_path = "/opt/intel/openvino/deployment_tools/open_model_zoo/tools/downloader/downloader.py"

env = os.environ.copy()
env['InferenceEngine_DIR'] = "/opt/intel/openvino/deployment_tools/inference_engine/share"
env['INTEL_OPENVINO_DIR'] = "/opt/intel/openvino"
env['OpenCV_DIR'] = "/opt/intel/openvino/opencv/cmake"
env[
    'LD_LIBRARY_PATH'] = "/opt/intel/openvino/opencv/lib:/opt/intel/openvino/deployment_tools/ngraph/lib:/opt/intel/opencl:/opt/intel/openvino/deployment_tools/inference_engine/external/hddl/lib:/opt/intel/openvino/deployment_tools/inference_engine/external/gna/lib:/opt/intel/openvino/deployment_tools/inference_engine/external/mkltiny_lnx/lib:/opt/intel/openvino/deployment_tools/inference_engine/external/tbb/lib:/opt/intel/openvino/deployment_tools/inference_engine/lib/intel64:"
env['HDDL_INSTALL_DIR'] = "/opt/intel/openvino/deployment_tools/inference_engine/external/hddl"
env['INTEL_CVSDK_DIR'] = "/opt/intel/openvino"
env['INSTALLDIR'] = "/opt/intel/openvino"
env[
    'PYTHONPATH'] = "/opt/intel/openvino/python/python3.6:/opt/intel/openvino/python/python3:/opt/intel/openvino/deployment_tools/open_model_zoo/tools/accuracy_checker:/opt/intel/openvino/deployment_tools/model_optimizer"
env[
    'PATH'] = "/opt/intel/openvino/deployment_tools/model_optimizer:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

UPLOAD_FOLDER = Path('/tmp/blobconverter')
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)


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
    print("Running command: {}".format(command))
    split_cmd = command.rstrip(' ').split(' ')
    try:
        proc = subprocess.Popen(split_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
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
    except Exception:
        raise CommandFailed(
            message=f"Command was unable to execute, command: {command}",
            payload=dict(
                stderr=traceback.format_exc(),
                stdout="",
                exit_code=-1
            )
        )


def request_myriad(workdir):
    definition_file = request.files.get('definition', None)
    weights_file = request.files.get('weights', None)
    extra_params = request.form.get('compile_flags', '')

    if definition_file is None:
        return "File named \"definition\" must be present in the request form", 400
    if weights_file is None:
        return "File named \"weights\" must be present in the request form", 400

    if Path(definition_file.filename).suffix != ".xml":
        return "Definitions file must have .xml extension", 400
    if Path(weights_file.filename).suffix != ".bin":
        return "Definitions file must have .bin extension", 400

    definitions_path = workdir / Path(secure_filename(definition_file.filename))
    weights_path = definitions_path.with_suffix('.bin')
    output_path = definitions_path.with_suffix('.blob')
    output_filename = Path(definition_file.filename).with_suffix('.blob').name

    definition_file.save(definitions_path)
    weights_file.save(weights_path)

    run_command(f"{compiler_path} -m {definitions_path} -o {output_path} {extra_params}")
    return send_file(output_path, as_attachment=True, attachment_filename=output_filename)


def request_zoo(workdir):
    model_name = request.form.get('model_name', '')
    model_downloader_params = request.form.get('model_downloader_params', '')
    command = f"{model_downloader_path} --name {model_name} --output_dir {workdir} --cache_dir {UPLOAD_FOLDER} {model_downloader_params}"
    run_command(command)
    if os.path.exists(f"{workdir}/public/{model_name}/{model_name}.caffemodel") or os.path.exists(f"{workdir}/public/{model_name}/{model_name}.tf"):
        intermediate_compiler_params = request.form.get('intermediate_compiler_params', '')
        command = f"{intermediate_compiler_path} --output_dir {workdir} --input_model {workdir}/public/{model_name}/{model_name}.caffemodel --input_proto {workdir}/public/{model_name}/{model_name}.prototxt {intermediate_compiler_params}"
        run_command(command)
        definitions_path = workdir
    else:
        definitions_path = f"{workdir}/intel/{model_name}/FP16"
    compiler_params = request.form.get('compiler_params', '')
    command = f"{compiler_path} -m {definitions_path}/{model_name}.xml -o {workdir}/model.blob {compiler_params}"
    run_command(command)
    return send_file(f"{workdir}/model.blob", as_attachment=True, attachment_filename=f"{model_name}.blob")


def request_model(workdir):
    model_type = request.form.get('model_type', '')
    intermediate_compiler_params = request.form.get('intermediate_compiler_params', '')
    model_file = request.files.get('model', None)
    proto_file = request.files.get('proto', None)

    model_path = workdir / Path(secure_filename(model_file.filename))
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
        command = f"{intermediate_compiler_path} --output_dir {workdir} --input_model {model_path} --input_proto {proto_path} {intermediate_compiler_params}"
        run_command(command)
    elif model_type == "tf":
        if model_file is None:
            return "File named \"model\" must be present in the request form", 400

        if Path(model_file.filename).suffix != ".pb":
            return "Model file must have .pb extension", 400

        model_file.save(model_path)
        command = f"{intermediate_compiler_path} --output_dir {workdir} --framework tf --input_model {model_path} {intermediate_compiler_params}"
        run_command(command)
    else:
        return jsonify(error=f"Invalid model type: {model_type}, supported: tf, caffe")

    compiler_params = request.form.get('compiler_params', '')
    command = f"{compiler_path} -m {definitions_path} -o {output_path} {compiler_params}"
    run_command(command)
    return send_file(output_path, as_attachment=True, attachment_filename=output_filename)


@app.errorhandler(CommandFailed)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.route("/", methods=['GET', 'POST'])
def parse():
    if request.method == 'GET':
        with open("/opt/intel/openvino/deployment_tools/inference_engine/version.txt") as version_f:
            version = version_f.readlines()
        return render_template('form.html', version=version)

    workdir = UPLOAD_FOLDER / Path(uuid.uuid4().hex)
    workdir.mkdir(parents=True, exist_ok=True)
    compile_type = request.form.get('compile_type', 'myriad')
    if compile_type == "myriad":
        return request_myriad(workdir)
    if compile_type == "model":
        return request_model(workdir)
    if compile_type == "zoo":
        return request_zoo(workdir)
    else:
        return jsonify(error=f"Unknown compile type: {compile_type}")


app.run(host='0.0.0.0', port=8080)
