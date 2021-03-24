import blobconverter

result = blobconverter.from_zoo("face-detection-retail-0004", shaves=5, use_cache=False)
print(result)

result = blobconverter.from_zoo("face-detection-retail-0004", shaves=5)
print(result)

result = blobconverter.from_caffe(
    proto="../../mobilenet-ssd.prototxt",  # get from https://drive.google.com/file/d/0B3gersZ2cHIxRm5PMWRoTkdHdHc
    model="../../mobilenet-ssd.caffemodel",  # get from https://raw.githubusercontent.com/chuanqi305/MobileNet-SSD/ba00fc987b3eb0ba87bb99e89bf0298a2fd10765/MobileNetSSD_deploy.prototxt
    data_type="FP16",
    shaves=5,
    use_cache=False,
)
print(result)

result = blobconverter.from_caffe(
    proto="../../mobilenet-ssd.prototxt",
    model="../../mobilenet-ssd.caffemodel",
    data_type="FP16",
    shaves=5,
)
print(result)

result = blobconverter.from_openvino(
    xml="../../face-detection-retail-0004.xml",  # get from https://storage.openvinotoolkit.org/repositories/open_model_zoo/2021.2/models_bin/3/face-detection-retail-0004/FP16/face-detection-retail-0004.xml
    bin="../../face-detection-retail-0004.bin",  # get from https://storage.openvinotoolkit.org/repositories/open_model_zoo/2021.2/models_bin/3/face-detection-retail-0004/FP16/face-detection-retail-0004.bin
    data_type="FP16",
    shaves=5,
    use_cache=False,
)
print(result)

result = blobconverter.from_openvino(
    xml="../../face-detection-retail-0004.xml",
    bin="../../face-detection-retail-0004.bin",
    data_type="FP16",
    shaves=5,
)
print(result)

result = blobconverter.from_tf(
    frozen_pb="../../deeplabv3_mnv2_pascal_train_aug.pb",  # get from http://download.tensorflow.org/models/deeplabv3_mnv2_pascal_train_aug_2018_01_29.tar.gz
    data_type="FP16",
    shaves=5,
    optimizer_params=[
        "--reverse_input_channels",
        "--input_shape=[1,513,513,3]",
        "--input=1:mul_1",
        "--output=ArgMax",
    ],
    use_cache=False,
)
print(result)

result = blobconverter.from_tf(
    frozen_pb="../../deeplabv3_mnv2_pascal_train_aug.pb",
    data_type="FP16",
    shaves=5,
    optimizer_params=[
        "--reverse_input_channels",
        "--input_shape=[1,513,513,3]",
        "--input=1:mul_1",
        "--output=ArgMax",
    ]
)
print(result)
