#!/bin/bash
set -x

sudo apt update 
sudo apt install python3.7-minimal python3-pip -y

#cd wheels/

python3.7 -m pip install *whl

