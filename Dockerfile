FROM openvino/ubuntu18_dev

USER root
RUN apt-get update && apt-get -y upgrade
RUN apt-get install -y python-dev python3-dev
USER openvino
RUN python3 -m pip install --upgrade tensorboard

ENV PYTHONUNBUFFERED 1
WORKDIR /app
ADD requirements.txt .
RUN python3 -m pip install -r requirements.txt

ADD templates templates
ADD main.py .
CMD ["python3", "main.py"]