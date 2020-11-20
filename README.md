# BlobConverter

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

## TODO

- cache myriad_compile
- customize precision (not only FP16)
- support additional output (not only .blob, also .xml and .bin)
- add advanced options for downloader / converter
- setup converter.luxonis.com domain
- add S3 backup
- make web UI responsive