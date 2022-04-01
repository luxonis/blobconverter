# BlobConverter API

[![Discord](https://img.shields.io/discord/790680891252932659?label=Discord)](https://discord.gg/luxonis)
[![Forum](https://img.shields.io/badge/Forum-discuss-orange)](https://discuss.luxonis.com/)
[![Docs](https://img.shields.io/badge/Docs-DepthAI-yellow)](https://docs.luxonis.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![](https://img.shields.io/pypi/v/blobconverter.svg)](https://pypi.org/project/blobconverter/)
[![Website](https://img.shields.io/badge/Website-BlobConverter-purpleblue)](http://blobconverter.luxonis.com/)

## Usage

- Docker-Compose

    ```
    docker-compose build
    docker-compose up
    ```

- Docker

    ```
    docker build -t blobconverter .
    docker run -p 8080:8080 blobconverter
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

## TODO

- customize precision (not only FP16)
- add advanced options for downloader / converter
