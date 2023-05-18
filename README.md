# BlobConverter API

[![Discord](https://img.shields.io/discord/790680891252932659?label=Discord)](https://discord.gg/luxonis)
[![Forum](https://img.shields.io/badge/Forum-discuss-orange)](https://discuss.luxonis.com/)
[![Docs](https://img.shields.io/badge/Docs-DepthAI-yellow)](https://docs.luxonis.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![](https://img.shields.io/pypi/v/blobconverter.svg)](https://pypi.org/project/blobconverter/)
[![Website](https://img.shields.io/badge/Website-BlobConverter-purpleblue)](http://blobconverter.luxonis.com/)

## Prepare

Download [OpenVINO with RVC3 support](https://drive.google.com/file/d/1IXtYi1Mwpsg3pr5cDXlEHdSUZlwJRTVP/view?usp=share_link), extract it to `openvino_files` and rename `install_dir` to `openvino2022_3_RVC3`.

## Usage

- Docker-Compose

    ```
    docker-compose build
    docker-compose up
    ```

- Docker

    ```
    docker build -t blobconverter .
    docker run -p 8000:8000 blobconverter
    ```

- System - python 3.5 or higher required

    ```
    pip install -r requirements.txt
    python main.py
    ```

## Building CLI

These steps will allow to build and push a new blobconverter CLI package to PyPi

```bash
rm dist/*
python setup.py sdist bdist_wheel
twine check dist/*
twine upload --username luxonis dist/*
```

## Testing locally

- Build and start the docker container (backend)

    ```
    docker build -t blobconverter .
    docker run -p 8000:8000 blobconverter
    ```

- Start the webserver (frontend)

    ```
    cd websrc
    yarn
    yarn start
    ```

## TODO

- customize precision (not only FP16)
- add advanced options for downloader / converter
