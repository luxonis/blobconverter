# BlobConverter API

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
