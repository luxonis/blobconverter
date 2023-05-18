#!/bin/bash
if [ ! -f /app/git/depthai-model-zoo ]
then
    cd /app/git/
    git clone https://github.com/luxonis/depthai-model-zoo
fi
cd /app/git/depthai-model-zoo
git reset --hard
git clean -dfx
git pull