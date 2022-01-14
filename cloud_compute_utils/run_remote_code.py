import paramiko

GITHUB = "https://github.com/RoyRin/cloud_compute_utils"


def get_install_cmd_str(github=GITHUB):
    """Get the command string to install cloud_compute_utils

    Args:
        github ([type], optional): github url. Defaults to https://github.com/RoyRin/cloud_compute_utils.

    Returns:
        [type]: [description]
    """
    github_dir = github.split("/")[-1]
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


def copy_cmd_to_file(cmd, filename):
    return f"echo \'{cmd}\' > {filename}"


def copy_files_to_instance(*, local_to_remote_filenames, hostname, username,
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


def run_command_on_instance(*,
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
    run_command_on_instance(command_str=command_str,
                            hostname=hostname,
                            username=username,
                            key_filepath=key_filepath)
