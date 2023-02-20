import json
import os
import glob
import shutil
from pathlib import Path
import hashlib
import yaml

def sha384sum(filename):
    h  = hashlib.sha384()
    b  = bytearray(128*1024)
    mv = memoryview(b)
    with open(filename, 'rb', buffering=0) as f:
        for n in iter(lambda : f.readinto(mv), 0):
            h.update(mv[:n])
    return h.hexdigest()

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

f = open("./models/intel_2022_1_RVC3.json", "r")
data = json.loads(f.read())
f.close()

#for model_name in data["available"]:
#    os.system(f"omz_downloader --name {model_name} --precisions FP16-INT8 --output_dir ./tmp")

#models_path = Path("./tmp/intel")
#for model in models_path.rglob("**/**/**/*.xml"):
#    os.system(f"/opt/intel/openvino_2022_kb/tools/compile_tool/compile_tool -d VPUX.3400 -m {model} -o {model.with_suffix('.blob')}")

models_path = Path("./tmp/intel")
output_path = Path("./tmp/processed")
BLOBCONVERTER_URL_ROOT = "https://blobconverter.nyc3.cdn.digitaloceanspaces.com/"

models_available_int8 = []
for model in models_path.rglob("**/**/**/*.blob"):
    model_name = model.parent.parent.stem
    model_name_q = f"{str(model_name)}-int8"
    (output_path / model_name).mkdir(parents=True, exist_ok=True)
    shutil.copy2(model.with_suffix(".xml"), output_path / model_name / (model_name_q + ".xml"))
    shutil.copy2(model.with_suffix(".bin"), output_path / model_name / (model_name_q + ".bin"))

    xml_file_path = output_path / model_name / (model_name_q + ".xml")
    bin_file_path = output_path / model_name / (model_name_q + ".bin")
    
    xml_file_bytesize = os.path.getsize(xml_file_path)
    bin_file_bytesize = os.path.getsize(bin_file_path)

    xml_file_checksum = sha384sum(xml_file_path)
    bin_file_checksum = sha384sum(bin_file_path)

    xml_file_url = BLOBCONVERTER_URL_ROOT + f"intel/2022_1/{model_name}/{model_name_q}.xml"
    bin_file_url = BLOBCONVERTER_URL_ROOT + f"intel/2022_1/{model_name}/{model_name_q}.bin"

    with open(Path("./models/2022_1/") / model_name / "model.yml", "r") as f:
        yaml_data = yaml.safe_load(f)

        for f in yaml_data["files"][::-1]:
            if f["name"].startswith("FP16-INT8"):
                yaml_data["files"].remove(f)

        yaml_data["files"].append({
            "name" : f"FP16-INT8/{model_name}.xml",
            "size": xml_file_bytesize,
            "checksum": xml_file_checksum,
            "source": xml_file_url
        })

        yaml_data["files"].append({
            "name" : f"FP16-INT8/{model_name}.bin",
            "size": bin_file_bytesize,
            "checksum": bin_file_checksum,
            "source": bin_file_url
        })
    
    models_available_int8.append(model_name)

    with open(Path("./models/2022_1/") / model_name / "model.yml", "w") as outfile:
        yaml.dump(yaml_data, outfile)
    
with open("./models/intel_2022_1_RVC3.json", "r") as f:
    data = json.loads(f.read())

models_available_fp16 = data["available"]
models_unavailable = ["unavailable"]
output = format_model_list(models_available_fp16, models_available_int8, models_unavailable)

with open("./models/intel_2022_1_RVC3_new.json", "w") as f:
    f.write(json.dumps(output, indent=4))