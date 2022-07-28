#!/usr/bin/env python

import yaml
import os
import urllib.request
import hashlib

def sha256sum(filename):
    h  = hashlib.sha256()
    b  = bytearray(128*1024)
    mv = memoryview(b)
    with open(filename, 'rb', buffering=0) as f:
        while n := f.readinto(mv):
            h.update(mv[:n])
    return h.hexdigest()


ZOO_DIRECTORY = "/app/depthai-model-zoo/models/"

for subdir, dirs, files in os.walk(ZOO_DIRECTORY):
    for file in files:
        if file.endswith(".yml"):
            with open(os.path.join(subdir, file), "r") as stream:
                try:
                    yml = yaml.safe_load(stream)
                    if 'files' in yml:
                        for blob_file in yml['files']:
                            if blob_file['name'].endswith('.bin'):
                                if 'source' in blob_file and 'sha256' in blob_file:
                                    blob_filename = blob_file['source'].split('/')[-1]
                                    blob_filepath = os.path.join(subdir, blob_filename)
                                    if not os.path.exists(blob_filepath) or sha256sum(blob_filepath) != blob_file['sha256']:
                                        try:
                                            with urllib.request.urlopen(blob_file['source']) as url:
                                                content = url.read()
                                                f = open(blob_filepath, "wb")
                                                f.write(content)
                                                f.close()
                                        except Exception as e:
                                            print(e)


                except yaml.YAMLError as exc:
                    print(exc)