import os
from pathlib import Path
import shutil
import sys
import json
import hashlib

def sha384sum(filename):
    h  = hashlib.sha384()
    b  = bytearray(128*1024)
    mv = memoryview(b)
    with open(filename, 'rb', buffering=0) as f:
        for n in iter(lambda : f.readinto(mv), 0):
            h.update(mv[:n])
    return h.hexdigest()



os.system("cd /tmp;omz_downloader --all -j20 --progress_format text")
os.system("cd /tmp;omz_converter --all --precisions FP16")



TARGET_DIR = Path("/tmp/converted_models")
TARGET_DIR = Path("/home/vlada/work/vscode/blobconverter_models/openvino_2022_1/")
TARGET_DIR.mkdir(parents=True, exist_ok=True)

BLOBCONVERTER_URL_ROOT = "https://blobconverter.nyc3.cdn.digitaloceanspaces.com/"

for path in Path("/tmp").rglob(f'**/FP16/*.xml'):
   
    model_name = path.parent.parent.name
    xml_file = path
    bin_file = path.parent / ( path.stem + ".bin"   )
    if not bin_file.exists():
        raise Exception("Could not find model")
    (TARGET_DIR / model_name).mkdir(parents=True, exist_ok=True)
    shutil.copy2(xml_file, TARGET_DIR / model_name)
    shutil.copy2(bin_file, TARGET_DIR / model_name)


with open('/tmp/myriad_config', 'w') as f:
    f.write('MYRIAD_NUMBER_OF_SHAVES 4\nMYRIAD_NUMBER_OF_CMX_SLICES 4\nMYRIAD_THROUGHPUT_STREAMS 1\nMYRIAD_ENABLE_MX_BOOT NO\n')


for path in Path(TARGET_DIR).rglob(f'**/*.xml'):
    blob_file = path.parent / (path.stem + ".blob")
    model_name = path.stem
    print(f"Processing model {model_name}")
    print(os.system(f"timeout 10m /opt/intel/openvino/tools/compile_tool/compile_tool -m {path} -o {blob_file} -c /tmp/myriad_config -d MYRIAD -ip U8"))

sorted_blob_list = {"available":sorted(x.stem.lower() for x in TARGET_DIR.rglob(f'**/*.blob'))}



OUTPUT_DIR = Path("./models/2022_1")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

with open(OUTPUT_DIR.parent / "openvino_2022_1.json", "w") as outfile:
    json.dump(sorted_blob_list, outfile)

for model_name in sorted_blob_list['available']:
    (OUTPUT_DIR / model_name).mkdir(parents=True, exist_ok=True)
    xml_file_path = TARGET_DIR / model_name/ (model_name + ".xml")
    bin_file_path = TARGET_DIR / model_name/ (model_name + ".bin")
    
    xml_file_bytesize = os.path.getsize (xml_file_path)
    bin_file_bytesize = os.path.getsize (bin_file_path)

    xml_file_checksum = sha384sum(xml_file_path)
    bin_file_checksum = sha384sum(bin_file_path)

    xml_file_url = BLOBCONVERTER_URL_ROOT + f"intel/2022_1/{model_name}/{model_name}.xml"
    bin_file_url = BLOBCONVERTER_URL_ROOT + f"intel/2022_1/{model_name}/{model_name}.bin"
    
    with open(OUTPUT_DIR / model_name/ "model.yml", "w") as outfile:
        outfile.write(f"""
description: empty
license: empty        
task_type: object_attributes
files:
  - name: FP16/{model_name}.xml
    size: {xml_file_bytesize}
    checksum: {xml_file_checksum}
    source: {xml_file_url}
  - name: FP16/{model_name}.bin
    size: {bin_file_bytesize}
    checksum: {bin_file_checksum}
    source: {bin_file_url}

framework: dldt 
        """)
    

