import requests
import json

ZOO_TYPE="intel"

url = "https://dev-blobconverter.luxonis.com/zoo_models"
params = {
    "version" : "2022.1",
    "zoo_type" : ZOO_TYPE
}
response = requests.get(url, params=params)
available = response.json()["available"]

url = "https://dev-blobconverter.luxonis.com/compile" 
rvc3 = {"available": [], "unavailable": []}
skippable = False
for model_dict in available:
    model = model_dict["name"]

    if model not in ["midasnet", "text-recognition-0015-encoder"]:
        print(f" --- {model} --- ")
        # change if running against other URL
        payload = {
            'use_zoo': True,
            'name': model,
            'data_type': 'FP16',
            'zoo_type': ZOO_TYPE,
            'compiler_params': '-ip U8'
        }
        params = {
            'version': '2022.3_RVC3',  # OpenVINO version, can be "2021.1", "2020.4", "2020.3", "2020.2", "2020.1", "2019.R3"
            'zoo_type': ZOO_TYPE
        }
        response = requests.post(url, data=payload, params=params)
    else:
        skippable = True
    print(response.status_code)

    if skippable or response.status_code != 200:
        f = open(f"./tmp8/{model}.txt", "a")
        f.write(response.text)
        f.close()
        skippable = False
        rvc3["unavailable"].append(model)
    else:
        rvc3["available"].append(model)

# save models
with open(f"./models/{ZOO_TYPE}_2022_3_RVC3_int8.json", "w") as outfile:
    outfile.write(json.dumps(rvc3, indent=4))