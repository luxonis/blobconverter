import os
import subprocess
import uuid
from pathlib import Path

from flask import Flask, request, jsonify, send_file, render_template
from werkzeug.utils import secure_filename

app = Flask(__name__)


compiler_path = "/opt/intel/openvino/deployment_tools/inference_engine/lib/intel64/myriad_compile"

# if not Path(compiler_path).exists():
#     raise RuntimeError("Unable to find \"myriad compile\" file in {}".format(compiler_path))
# else:
#     print("Using myriad_compile: {}".format(compiler_path))

UPLOAD_FOLDER = Path('/tmp/blobconverter')
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)


@app.route("/", methods=['GET', 'POST'])
def parse():
    if request.method == 'GET':
        with open("/opt/intel/openvino/deployment_tools/inference_engine/version.txt") as version_f:
            version = version_f.readlines()
        return render_template('form.html', version=version)

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

    definitions_path = UPLOAD_FOLDER / Path(uuid.uuid4().hex + secure_filename(definition_file.filename))
    weights_path = definitions_path.with_suffix('.bin')
    output_path = definitions_path.with_suffix('.blob')
    output_filename = Path(definition_file.filename).with_suffix('.blob').name

    definition_file.save(definitions_path)
    weights_file.save(weights_path)

    command = "{compiler} -m {definition} -o {output} {extra}".format(
        compiler=compiler_path, definition=definitions_path, output=output_path, extra=extra_params
    ).rstrip(' ').split(' ')
    print("Running command: {}".format(command))
    env = os.environ.copy()
    env['InferenceEngine_DIR'] = "/opt/intel/openvino/deployment_tools/inference_engine/share"
    env['INTEL_OPENVINO_DIR'] = "/opt/intel/openvino"
    env['OpenCV_DIR'] = "/opt/intel/openvino/opencv/cmake"
    env['LD_LIBRARY_PATH'] = "/opt/intel/openvino/opencv/lib:/opt/intel/openvino/deployment_tools/ngraph/lib:/opt/intel/opencl:/opt/intel/openvino/deployment_tools/inference_engine/external/hddl/lib:/opt/intel/openvino/deployment_tools/inference_engine/external/gna/lib:/opt/intel/openvino/deployment_tools/inference_engine/external/mkltiny_lnx/lib:/opt/intel/openvino/deployment_tools/inference_engine/external/tbb/lib:/opt/intel/openvino/deployment_tools/inference_engine/lib/intel64:"
    env['HDDL_INSTALL_DIR'] = "/opt/intel/openvino/deployment_tools/inference_engine/external/hddl"
    env['INTEL_CVSDK_DIR'] = "/opt/intel/openvino"
    env['INSTALLDIR'] = "/opt/intel/openvino"
    env['PYTHONPATH'] = "/opt/intel/openvino/python/python3.6:/opt/intel/openvino/python/python3:/opt/intel/openvino/deployment_tools/open_model_zoo/tools/accuracy_checker:/opt/intel/openvino/deployment_tools/model_optimizer"
    env['PATH'] = "/opt/intel/openvino/deployment_tools/model_optimizer:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
    proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
    stdout, stderr = proc.communicate()
    print("Command returned exit code: {}".format(proc.returncode))

    if proc.returncode != 0:
        return jsonify(
            command=' '.join(command),
            stderr=stderr.decode(),
            stdout=stdout.decode(),
            exit_code=proc.returncode
        ), 500
    else:
        return send_file(output_path, as_attachment=True, attachment_filename=output_filename)


app.run(host='0.0.0.0', port=8080)
