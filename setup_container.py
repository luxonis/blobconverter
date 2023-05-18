import os
import subprocess
from pathlib import Path

versions = {
    "2022_3_RVC3" : Path("/opt/intel/openvino2022_3_RVC3/python/python3.8/requirements.txt"),
    "2022_1": Path("/opt/intel/openvino2022_1/tools/requirements.txt"),
    "2021_4": Path("/opt/intel/openvino2021_4/deployment_tools/model_optimizer/requirements.txt"),
    "2021_3": Path("/opt/intel/openvino2021_3/deployment_tools/model_optimizer/requirements.txt"),
    "2021_2": Path("/opt/intel/openvino2021_2/deployment_tools/model_optimizer/requirements.txt"),
    "2021_1": Path("/opt/intel/openvino2021_1/deployment_tools/model_optimizer/requirements.txt"),
    "2020_4": Path("/opt/intel/openvino2020_4/deployment_tools/model_optimizer/requirements.txt"),
}
additional_packages = ["pyyaml"]


def abs_str(path: Path):
    return str(path.absolute())


def create_venv(name: str, req_path: Path, interpreter):

    venv_path = Path("/app") / "venvs" / ("venv"+name)
    venv_python_path = venv_path / "bin" / "python"
    venv_path.parent.mkdir(parents=True, exist_ok=True)
    new_env = os.environ.copy()
    if "PYTHONHOME" in new_env:
        del new_env["PYTHONHOME"]
    new_env["VIRTUAL_ENV"] = abs_str(venv_path)
    new_env["PATH"] = abs_str(venv_path / "bin") + ":" + new_env["PATH"]
    subprocess.check_call([interpreter, "-m", "venv", abs_str(venv_path)])
    subprocess.check_call([abs_str(venv_python_path), "-m", "pip", "install", "-U", "pip"], env=new_env)
    subprocess.check_call([abs_str(venv_python_path), "-m", "pip", "install", "-r", abs_str(req_path)], env=new_env)
    subprocess.check_call([abs_str(venv_python_path), "-m", "pip", "install", *additional_packages], env=new_env)

    if name in ["2021_4"]:
        subprocess.check_call([abs_str(venv_python_path), "-m", "pip", "install", "openvino-dev[all]==2021.4.2", "openvino-dev[tensorflow2,mxnet,caffe,pytorch]==2021.4.2", "protobuf==3.15.6"], env=new_env)
    if name in ["2022_1"]:
        subprocess.check_call([abs_str(venv_python_path), "-m", "pip", "install", "openvino-dev[all]==2022.1.0", "openvino-dev[tensorflow2,mxnet,caffe,pytorch]==2022.1.0", "protobuf==3.15.6"], env=new_env)
    if name in ["2022_3_RVC3"]:
        subprocess.check_call([abs_str(venv_python_path), "-m", "pip", "install", "openvino-dev==2022.3", "protobuf==3.15.6"], env=new_env)


if __name__ == "__main__":
    for env_name, base_path in versions.items():
        create_venv(env_name, base_path, "python3.8")

