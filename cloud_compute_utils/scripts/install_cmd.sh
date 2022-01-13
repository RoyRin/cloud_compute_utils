#!/bin/bash
set -x
sudo apt update
sudo apt install -y python3-pip
#curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python3 -
cd $HOME
git clone https://github.com/RoyRin/cloud_compute_utils
pip install cloud_compute_utils

#poetry shell
#poetry install
echo "hello"