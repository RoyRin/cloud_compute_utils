import paramiko
from pathlib import Path
import os

GITHUB = "https://github.com/RoyRin/cloud_compute_utils"


def get_wheels(wheel_dir):
    """
    Get all the wheels in the wheel_dir
    """
    return [
        os.path.join(wheel_dir, filename) for filename in os.listdir(wheel_dir)
        if filename.endswith(".whl")
    ]


def install_remotely_whl(*,
                         hostname,
                         key_filepath,
                         wheel_dir=Path(__file__).parent.parent / "dist",
                         username="ubuntu",
                         verbose=True):
    """
    install the code on the remote instances, using wheels
        Note: wheel needs to exist in the wheel_dir
    
    """
    wheels = get_wheels(wheel_dir)
    if len(wheels) == 0:
        raise ValueError(f"No wheels found in {wheel_dir}")

    wheel_path = sorted(wheels)[-1]

    remote_wheel_path = os.path.join("/home/ubuntu/",
                                     os.path.basename(wheel_path))
    local_to_remote_filenames = {wheel_path: remote_wheel_path}

    copy_files_to_instance(local_to_remote_filenames=local_to_remote_filenames,
                           hostname=hostname,
                           username=username,
                           key_filepath=key_filepath)

    bash_cmd = f"""
#!/bin/bash
set -x
sudo apt update && sudo apt install python3-pip -y
python3 -m pip install {remote_wheel_path} """
    if verbose:
        print(bash_cmd)
    run_bash_on_instance(command_strings=[bash_cmd],
                         hostname=hostname,
                         username=username,
                         key_filepath=key_filepath)


def copy_cmd_to_file(cmd, filename):
    return f"echo \'{cmd}\' > {filename}"


def copy_files_to_instance(*,
                           local_to_remote_filenames,
                           hostname,
                           username="ubuntu",
                           key_filepath):
    """
    Copies files to instance
    Args:
        local_to_remote_filenames ([dict]): maps local filenames to remote filenames
        hostname ([type]): [description]
        username ([type]): [description]
        key_filepath ([type], optional): [description]. Defaults to key_filepath.

    Returns:
        [type]: [description]
    """

    # Connect to remote host
    with paramiko.SSHClient() as client:
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname, username=username, key_filename=key_filepath)

        # Setup sftp connection and transmit this script
        with client.open_sftp() as sftp:
            for local_filename, remote_filename in local_to_remote_filenames.items(
            ):
                sftp.put(local_filename, remote_filename)

    client.close()


def run_command_helper(client, cmd, verbose=False):
    return_strings = []
    stdin, stdout, stderr = client.exec_command(cmd)

    if len(list(stderr)) != 0:
        print("Error!")
        print(stderr.readlines())
        for line in stderr:
            print(line)

    for line in stdout:
        if verbose:
            print(f"{line}")
        return_strings.append(line)

    return return_strings


def run_bash_on_instance(*,
                         command_strings,
                         hostname,
                         username,
                         key_filepath,
                         verbose=False):
    """ runs a command on an instance """
    return_strings = []
    # Connect to remote host
    with paramiko.SSHClient() as client:
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname, username=username, key_filename=key_filepath)
        for cmd in command_strings:
            return_strings += run_command_helper(client, cmd, verbose=verbose)
    return return_strings


def _run_this_file_on_instance(hostname, username, key_filepath):
    """
    Run this file specific file on an instance.
        (Somewhat of a niche thing to do.)
    """
    local_to_remote_filenames = {__file__: "/tmp/myscript.py"}
    command_str = "python3 /tmp/myscript.py"
    copy_files_to_instance(local_to_remote_filenames=local_to_remote_filenames,
                           hostname=hostname,
                           username=username,
                           key_filepath=key_filepath)
    run_bash_on_instance(command_str=command_str,
                         hostname=hostname,
                         username=username,
                         key_filepath=key_filepath)


def install_remotely_from_src(
        *,
        hostname,
        key_filepath,
        local_git_token_path=Path(__file__).parent.parent / "secrets" /
    "royrin_GIT_TOKEN.txt",
        username="ubuntu",
        GIT_USERNAME="RoyRin",
        GIT_REPOSITORY="neural_nets_memorization",
        verbose=True):
    """
    install the code on the remote instances
    
    """
    remote_BASE_DIR = Path("/home/ubuntu/")

    remote_PROJECT_PATH = os.path.join(remote_BASE_DIR, GIT_REPOSITORY)
    remote_GIT_TOKEN_path = os.path.join(remote_BASE_DIR,
                                         "royrin_GIT_TOKEN.txt")
    local_to_remote_filenames = {local_git_token_path: remote_GIT_TOKEN_path}

    copy_files_to_instance(local_to_remote_filenames=local_to_remote_filenames,
                           hostname=hostname,
                           username=username,
                           key_filepath=key_filepath)

    bash_cmd = f"""
#!/bin/bash
set -x
sudo apt update && sudo apt install python3-pip -y
rm -rf "{remote_PROJECT_PATH}"
mkdir "{remote_PROJECT_PATH}"
cat {remote_GIT_TOKEN_path}
git clone --recurse-submodules https://`cat {remote_GIT_TOKEN_path}`@github.com/{GIT_USERNAME}/{GIT_REPOSITORY}.git "{remote_PROJECT_PATH}"
cd {remote_PROJECT_PATH}
python3 -m pip install . """
    if verbose:
        print(bash_cmd)
    run_bash_on_instance(command_strings=[bash_cmd],
                         hostname=hostname,
                         username=username,
                         key_filepath=key_filepath)
