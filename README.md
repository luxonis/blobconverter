# BlobConverter API

[![Discord](https://img.shields.io/discord/790680891252932659?label=Discord)](https://discord.gg/luxonis)
[![Forum](https://img.shields.io/badge/Forum-discuss-orange)](https://discuss.luxonis.com/)
[![Docs](https://img.shields.io/badge/Docs-DepthAI-yellow)](https://docs.luxonis.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![](https://img.shields.io/pypi/v/blobconverter.svg)](https://pypi.org/project/blobconverter/)
[![Website](https://img.shields.io/badge/Website-BlobConverter-purpleblue)](http://blobconverter.luxonis.com/)

## Usage

First, download RVC3 files from [here](https://drive.google.com/file/d/1NTN2AX8yLcn7Jvk077Fq8lYsYyLAK-ve) and extract them to `./openvino_files/openvino2022_1_RVC3/`.

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
