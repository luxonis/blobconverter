FROM node:10.16 as web

COPY websrc/ websrc/
WORKDIR websrc/
RUN yarn
RUN yarn build

FROM openvino/ubuntu18_dev:2021.1

COPY --from=openvino/ubuntu18_dev:2020.1 /opt/intel/openvino /opt/intel/openvino2020_1
COPY --from=openvino/ubuntu18_dev:2020.4 /opt/intel/openvino /opt/intel/openvino2020_4
COPY --from=openvino/ubuntu18_dev:2020.3 /opt/intel/openvino /opt/intel/openvino2020_3
COPY --from=openvino/ubuntu18_dev:2020.2 /opt/intel/openvino /opt/intel/openvino2020_2
COPY --from=openvino/ubuntu18_dev:2019_R3.1 /opt/intel/openvino /opt/intel/openvino2019_3

USER root
RUN apt-get update && apt-get -y upgrade
RUN apt-get install -y python-dev python3-dev
USER openvino
ADD requirements_openvino.txt .
RUN python3 -m pip install -r requirements_openvino.txt
RUN python3 -m pip install --upgrade tensorboard

ENV PYTHONUNBUFFERED 1
WORKDIR /app
ADD requirements.txt .
RUN python3 -m pip install -r requirements.txt

COPY --from=web websrc/build/ websrc/build/
ADD main.py .
CMD ["python3", "main.py"]