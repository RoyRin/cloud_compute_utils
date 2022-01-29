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
                         install_script=Path(__file__).parent / "scripts" /
                         "install.sh",
                         username="ubuntu",
                         remote_base="/home/ubuntu/",
                         verbose=True):
    """
    install the code on the remote instances, using wheels
        Note: wheel needs to exist in the wheel_dir
    
    """
    wheels = get_wheels(wheel_dir)
    if len(wheels) == 0:
        raise ValueError(f"No wheels found in {wheel_dir}")

    local_to_remote_filenames = {
        wheel_path: os.path.join(remote_base, os.path.basename(wheel_path))
        for wheel_path in wheels
    }
    local_to_remote_filenames[install_script] = os.path.join(
        remote_base, "install.sh")

    # remove the existing wheel files if they exists
    if verbose:
        print("Removing existing wheels")
    rm_cmd = f""" rm {os.path.join(remote_base, '*whl')} 2> /dev/null """
    results = run_bash_on_instance(command_strings=[rm_cmd],
                                   hostname=hostname,
                                   username=username,
                                   key_filepath=key_filepath,
                                   verbose=True)

    if verbose:
        print("Copying files to remote instance")
    copy_files_to_instance(local_to_remote_filenames=local_to_remote_filenames,
                           hostname=hostname,
                           username=username,
                           key_filepath=key_filepath)

    bash_cmd = f""" bash {remote_base}/install.sh """

    if verbose:
        print("running install script")
    results = run_bash_on_instance(command_strings=[bash_cmd],
                                   hostname=hostname,
                                   username=username,
                                   key_filepath=key_filepath,
                                   verbose=True)
    return results


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


def run_command_helper(client, cmd, blocking=True, verbose=False):
    results = {"stdout": [], "stderr": []}
    stdin, stdout, stderr = client.exec_command(cmd)
    if blocking:  # im not sure this is working.
        exit_status = stdout.channel.recv_exit_status()  # Blocking call
        if verbose:
            if exit_status == 0:
                print("Command successful")
            else:
                print("Error", exit_status)
        stderr = stderr.readlines()

        for line in stderr:
            results["stderr"].append(line)

        stdout = stdout.readlines()
        for line in stdout:
            results["stdout"].append(line)

    return results


def print_bash_results(results):
    """ print results from the run_command_helper"""
    for key, value in results.items():
        print(f"{key}:")
        for line in value:
            print(f"\t{line}")


def run_bash_on_instance(*,
                         command_strings,
                         hostname,
                         username,
                         key_filepath,
                         blocking=True,
                         verbose=True):
    """ runs a command on an instance """
    return_strings = {}
    # Connect to remote host
    with paramiko.SSHClient() as client:
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname, username=username, key_filename=key_filepath)
        for cmd in command_strings:
            res = run_command_helper(client,
                                     cmd,
                                     blocking=blocking,
                                     verbose=verbose)

            for k, v in res.items():
                if return_strings.get(k) is None:
                    return_strings[k] = []
                return_strings[k].append(v)
    if verbose:
        print_bash_results(return_strings)
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
    res = run_bash_on_instance(command_str=command_str,
                               hostname=hostname,
                               username=username,
                               key_filepath=key_filepath)


def __install_remotely_from_src(
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
    -- to remove soon
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
