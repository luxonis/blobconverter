import os
import subprocess
import sys
from pathlib import Path

versions = {
    "2021_4": Path("/opt/intel/openvino_2021"),
    "2021_3": Path("/opt/intel/openvino2021_3"),
    "2021_2": Path("/opt/intel/openvino2021_2"),
    "2021_1": Path("/opt/intel/openvino2021_1"),
    "2020_4": Path("/opt/intel/openvino2020_4"),
    "2020_3": Path("/opt/intel/openvino2020_3"),
    "2020_2": Path("/opt/intel/openvino2020_2"),
    "2020_1": Path("/opt/intel/openvino2020_1"),
    "2019_3": Path("/opt/intel/openvino2019_3"),
}


def abs_str(path: Path):
    return str(path.absolute())


def create_venv(name: str, path: Path):
    req_path = path / "deployment_tools" / "model_optimizer" / "requirements.txt"
    venv_path = Path("/app") / "venvs" / ("venv"+name)
    venv_python_path = venv_path / "bin" / "python"
    venv_path.parent.mkdir(parents=True, exist_ok=True)
    new_env = os.environ.copy()
    if "PYTHONHOME" in new_env:
        del new_env["PYTHONHOME"]
    new_env["VIRTUAL_ENV"] = abs_str(venv_path)
    new_env["PATH"] = abs_str(venv_path / "bin") + ":" + new_env["PATH"]
    subprocess.check_call([sys.executable, "-m", "venv", abs_str(venv_path)])
    subprocess.check_call([abs_str(venv_python_path), "-m", "pip", "install", "-U", "pip"], env=new_env)
    subprocess.check_call([abs_str(venv_python_path), "-m", "pip", "install", "-r", abs_str(req_path)], env=new_env)


if __name__ == "__main__":
    for env_name, base_path in versions.items():
        create_venv(env_name, base_path)

