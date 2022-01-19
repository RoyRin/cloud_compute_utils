#from cloud_compute_utils import aws_util

from cloud_compute_utils import run_remote_code
from cloud_compute_utils import aws_util
"""Todo:
    2. save code to s3 bucket
    1. write a decorator function that writes the function to s3
        1. function needs to return dict
        2. function needs to return numpy array

    3. change the size of instances
"""

key_filepath = "/home/roy/code/research/cloud_compute_utils/secrets/ec2-keypair.pem"
github = "https://github.com/RoyRin/cloud_compute_utils"
github_dir = "cloud_compute_utils"


def get_install_cmd_str():
    return f'''
#!/bin/bash
set -x
sudo apt update
sudo apt install -y python3-pip

cd $HOME
rm -rf {github_dir} 
git clone {github}
cd {github_dir}
pip install .
    '''


def get_run_cmd_str():
    return '''
#!/bin/bash
set -x

cd $HOME
cd cloud_compute_utils
echo `/home/ubuntu/.local/bin/cloud-cli` > cloud-cli.txt
    '''


def _get_instance_dns_name():
    """ Helper function to get the instance dns name """
    ec2 = aws_util.get_ec2_client()
    running_instances = aws_util.get_running_instances(ec2)
    instance = running_instances[0]
    aws_util.print_instance(instance)
    hostname = instance.public_dns_name
    username = "ubuntu"
    return hostname, username


# TODO(Roy) on 2022-01-13: catch execute command to see what error code it returns

if __name__ == '__main__':
    hostname, username = _get_instance_dns_name()

    cmd1 = run_remote_code.copy_cmd_to_file(get_install_cmd_str(),
                                            "/tmp/install_cmd.sh")
    cmd2 = run_remote_code.copy_cmd_to_file(get_run_cmd_str(),
                                            "/tmp/run_cmd.sh")
    install_cmd_str = "bash /tmp/install_cmd.sh"
    run_cmd_str = "bash /tmp/run_cmd.sh"

    run_remote_code.run_bash_on_instance(
        command_strings=[cmd1, cmd2, install_cmd_str, run_cmd_str],
        hostname=hostname,
        username=username,
        key_filepath=key_filepath,
        verbose=True)
