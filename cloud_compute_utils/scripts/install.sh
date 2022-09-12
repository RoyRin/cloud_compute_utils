#!/bin/bash
set -x
source /home/ubuntu/anaconda3/bin/activate

find_in_conda_env(){
    conda env list | grep "${@}" >/dev/null 2>/dev/null
}

if find_in_conda_env "py_39_jax" ; then
   conda activate py_39_jax
else 
    conda create -n py_39_jax python=3.9
    conda activate py_39_jax
    conda install -c conda-forge pip
fi

for wheel in `ls | grep "whl"`; do 
	echo "installing $wheel"
	echo "\n\n\n\n\n"
	pip install $wheel --force-reinstall
	echo "\n-------done"
	echo "\n\n\n\n\n"
done


#
# Hack - manually instal dp-accounting
#
"""dp_accounting @ git+https://github.com/google/differential-privacy/#egg=dp-accounting&subdirectory=python""" > requirements_tmp.txt
pip install -r requirements_tmp.txt
