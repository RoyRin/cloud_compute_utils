#from cloud_compute_utils import aws_util

import sys
import os
from pathlib import Path
import socket
from cloud_compute_utils import run_remote_code
from cloud_compute_utils import aws_util
"""Todo:
    2. save code to s3 bucket
    1. write a decorator function that writes the function to s3
        1. function needs to return dict
        2. function needs to return numpy array
"""

key_filepath = "/home/roy/code/research/cloud_compute_utils/secrets/ec2-keypair.pem"
github = "https://github.com/RoyRin/cloud_compute_utils"
github_dir = "cloud_compute_utils"


def run_this_file_on_instance(hostname, username, key_filepath):
    """
    Run this file on an instance.
    """
    local_to_remote_filenames = {__file__: "/tmp/myscript.py"}
    command_str = "python3 /tmp/myscript.py"
    run_remote_code.copy_files_to_instance(
        local_to_remote_filenames=local_to_remote_filenames,
        hostname=hostname,
        username=username,
        key_filepath=key_filepath)
    run_remote_code.run_command_on_instance(command_str=command_str,
                                            hostname=hostname,
                                            username=username,
                                            key_filepath=key_filepath)


def get_run_cmd_str():
    return '''
#!/bin/bash
set -x

cd $HOME
cd cloud_compute_utils
echo `/home/ubuntu/.local/bin/deployments-cli` > deployments-cli.txt
    '''


def get_install_cmd_str():
    return '''
#!/bin/bash
set -x
sudo apt update
sudo apt install -y python3-pip

cd $HOME
git clone https://github.com/RoyRin/cloud_compute_utils
pip install cloud_compute_utils
    '''


def copy_cmd_to_file(cmd, filename):
    return f"echo \'{cmd}\' > {filename}"


if __name__ == '__main__':
    ec2 = aws_util.get_ec2_client()
    running_instances = aws_util.get_running_instances(ec2)
    hostname = running_instances[0].public_dns_name
    username = "ubuntu"

    aws_util.print_instance(running_instances[0])

    basedir = Path(__file__).parent.resolve()
    scripts_dir = basedir / "scripts"
    print(scripts_dir)

    local_to_remote_filenames = {
        os.path.join(scripts_dir, "install_cmd.sh"):
        os.path.join("/tmp", "install_cmd.sh"),
        os.path.join(scripts_dir, "run.sh"):
        os.path.join("/tmp", "run.sh"),
    }

    install_str = "bash /tmp/install_cmd.sh"
    run_str = "bash /tmp/run_cmd.sh"

    s = f"my name is Roy {basedir}"
    cmd = f"echo \"{s}\" > /tmp/my_file.txt"
    cmd1 = copy_cmd_to_file(get_install_cmd_str(), "/tmp/install_cmd.sh")
    cmd2 = copy_cmd_to_file(get_run_cmd_str(), "/tmp/run_cmd.sh")
    run_remote_code.run_command_on_instance(
        command_strings=[cmd1, cmd2, install_str, run_str],
        hostname=hostname,
        username=username,
        key_filepath=key_filepath,
        verbose=True)
