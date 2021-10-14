FROM node:10.16 as web

COPY websrc/ websrc/
WORKDIR websrc/
RUN yarn
RUN yarn build

FROM openvino/ubuntu20_dev:2021.4

COPY --from=openvino/ubuntu20_dev:2021.3 /opt/intel/openvino /opt/intel/openvino2021_3
COPY --from=openvino/ubuntu18_dev:2021.2 /opt/intel/openvino /opt/intel/openvino2021_2
COPY --from=openvino/ubuntu18_dev:2021.1 /opt/intel/openvino /opt/intel/openvino2021_1
COPY --from=openvino/ubuntu18_dev:2020.4 /opt/intel/openvino /opt/intel/openvino2020_4
COPY --from=openvino/ubuntu18_dev:2020.3 /opt/intel/openvino /opt/intel/openvino2020_3
COPY --from=openvino/ubuntu18_dev:2020.2 /opt/intel/openvino /opt/intel/openvino2020_2
COPY --from=openvino/ubuntu18_dev:2020.1 /opt/intel/openvino /opt/intel/openvino2020_1
COPY --from=openvino/ubuntu18_dev:2019_R3.1 /opt/intel/openvino /opt/intel/openvino2019_3

USER root
RUN apt-get update && apt-get -y upgrade && apt-get install -y software-properties-common
RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt-get update
RUN apt-get install -y python3-dev nano git git-lfs python3.7 python3.7-venv
ADD patch_openvino.py /opt/intel
ADD models_gdrive.patch /opt/intel
RUN python3 /opt/intel/patch_openvino.py
WORKDIR /app
RUN chown openvino:openvino /app
USER openvino
ENV PYTHONUNBUFFERED 1

RUN git lfs install
RUN git clone https://github.com/luxonis/depthai-model-zoo.git

ADD setup_container.py .
RUN python3 setup_container.py
ADD docker_scheduled.sh .
ADD requirements.txt .
ADD model_compiler model_compiler
RUN python3 -m pip install -r requirements.txt

COPY --from=web websrc/build/ websrc/build/
ADD main.py .
CMD ["python3", "-m", "gunicorn", "--chdir", "/app", "main:app", "-w", "2", "--threads", "2", "-b", "0.0.0.0:8000"]