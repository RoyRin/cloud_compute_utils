#from cloud_compute_utils import aws_util
import paramiko
import sys
import os
import socket
from cloud_compute_utils import run_remote_code
from cloud_compute_utils import aws_util
"""

1. run function on instance
2. save code to s3 bucket

to do: for the instances, have them be a specific size; have them mount to a specific bucket
    1. pass arguments (in this case, the indicies of the data), 
    2. pull code from github,  run poetry install
    which takes indices as an argument, 


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


def helper():
    print(os.name)
    print(socket.gethostname())


if __name__ == '__main__':
    """
    try:

        if sys.argv[1] == 'deploy':
            command_str = "python3 /tmp/myscript.py"
            run_this_file_on_instance(hostname=hostname,
                                      username=username,
                                      key_filepath=key_filepath)
            sys.exit(0)
    except IndexError:
        pass
    """

    ec2 = aws_util.get_ec2_client()
    running_instances = aws_util.get_running_instances(ec2)
    hostname = running_instances[0].public_dns_name
    #hostname = "ec2-44-201-236-146.compute-1.amazonaws.com"
    username = "ubuntu"

    aws_util.print_instance(running_instances[0])

    install_cmds = [
        #"sudo apt update", "sudo apt install -y python3-pip",
        #"curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python3 -",
        "pwd",
        f"git clone {github}",
        f"cd {github_dir}",
        "ls",
        f"poetry shell",
        "poetry install",
        f"deployment-cli --help"
    ]
    local_to_remote_filenames = {
        "/home/roy/code/research/cloud_compute_utils/cloud_compute_utils/scripts/install_cmd.sh":
        "/tmp/install.sh",
        "/home/roy/code/research/cloud_compute_utils/cloud_compute_utils/scripts/run.sh":
        "/tmp/run.sh"
    }

    command_str_install = "bash /tmp/install_cmd.sh"
    command_str_run = "bash /tmp/run.sh"
    run_remote_code.copy_files_to_instance(
        local_to_remote_filenames=local_to_remote_filenames,
        hostname=hostname,
        username=username,
        key_filepath=key_filepath)

    run_remote_code.run_command_on_instance(
        command_strings=[command_str_install, command_str_run],
        hostname=hostname,
        username=username,
        key_filepath=key_filepath,
        verbose=True)
    """command_str
    run_remote_code.run_command_on_instance(command_strings=install_cmds,
                                            hostname=hostname,
                                            username=username,
                                            key_filepath=key_filepath,
                                            verbose=True)

    """