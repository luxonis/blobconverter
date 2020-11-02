export const openvino = `import requests

url = "${window.location.origin}/compile"  # change if running against other URL

payload = {
    'compiler_params': '-ip U8 -VPU_MYRIAD_PLATFORM VPU_MYRIAD_2480 -VPU_NUMBER_OF_SHAVES 4 -VPU_NUMBER_OF_CMX_SLICES 4',
    'compile_type': 'myriad'
}
files = {
    'definition': open('/path/to/definition.xml', 'rb'),
    'weights': open('/path/to/weights.bin', 'rb')
}
params = {
    'version': '2020.1',  # OpenVINO version, can be "2021.1", "2020.4", "2020.3", "2020.2", "2020.1", "2019.R3"
}

response = requests.post(url, data=payload, files=files, params=params)
`

export const caffe = `import requests

url = "${window.location.origin}/compile"  # change if running against other URL
payload = {
    'compile_type': 'model',
    'model_type': 'caffe',
    'intermediate_compiler_params': '--data_type=FP16 --mean_values [127.5,127.5,127.5] --scale_values [255,255,255]',
    'compiler_params': '-ip U8 -VPU_MYRIAD_PLATFORM VPU_MYRIAD_2480 -VPU_NUMBER_OF_SHAVES 4 -VPU_NUMBER_OF_CMX_SLICES 4'
}
files = {
    'model': open('/path/to/mobilenet-ssd.caffemodel', 'rb'),
    'proto': open('/path/to/mobilenet-ssd.prototxt', 'rb')
}
params = {
    'version': '2020.1',  # OpenVINO version, can be "2021.1", "2020.4", "2020.3", "2020.2", "2020.1", "2019.R3"
}
response = requests.post(url, data=payload, files=files, params=params)
`

export const tf = `import requests

url = "${window.location.origin}/compile"  # change if running against other URL
payload = {
    'compile_type': 'model',
    'model_type': 'caffe',
    'intermediate_compiler_params': '--data_type=FP16 --mean_values [127.5,127.5,127.5] --scale_values [255,255,255]',
    'compiler_params': '-ip U8 -VPU_MYRIAD_PLATFORM VPU_MYRIAD_2480 -VPU_NUMBER_OF_SHAVES 4 -VPU_NUMBER_OF_CMX_SLICES 4'
}
files = {
    'model': open('/path/to/mobilenet-ssd.pb', 'rb'),
}
params = {
    'version': '2020.1',  # OpenVINO version, can be "2021.1", "2020.4", "2020.3", "2020.2", "2020.1", "2019.R3"
}
response = requests.post(url, data=payload, files=files, params=params)
`

export const zoo = `import requests

url = "${window.location.origin}/compile"  # change if running against other URL
payload = {
    'compile_type': 'zoo',
    'model_name': 'mobilenet-ssd',
    'model_downloader_params': '--precisions FP16 --num_attempts 5',
    'intermediate_compiler_params': '--data_type=FP16 --mean_values [127.5,127.5,127.5] --scale_values [255,255,255]',
    'compiler_params': '-ip U8 -VPU_MYRIAD_PLATFORM VPU_MYRIAD_2480 -VPU_NUMBER_OF_SHAVES 4 -VPU_NUMBER_OF_CMX_SLICES 4'
}
params = {
    'version': '2020.1',  # OpenVINO version, can be "2021.1", "2020.4", "2020.3", "2020.2", "2020.1", "2019.R3"
}
response = requests.post(url, data=payload, params=params)
`