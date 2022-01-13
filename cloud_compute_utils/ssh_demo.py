
import sys
import os

import socket 



def main():
    print(os.name)
    print(socket.gethostname())

hostname = "ec2-3-86-60-190.compute-1.amazonaws.com"
username = "ec2-user"
key_filename = "/home/roy/code/research/cloud_compute_utils/secrets/ec2-keypair.pem"

if __name__ == '__main__':
    try:
        
        if sys.argv[1] == 'deploy':
            import paramiko

            # Connect to remote host
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            #client.connect('remote_hostname_or_IP', username='john', password='secret')

            client.connect(hostname, username=username, key_filename=key_filename)
            
            # Setup sftp connection and transmit this script
            sftp = client.open_sftp()
            sftp.put(__file__, '/tmp/myscript.py')
            sftp.close()

            # Run the transmitted script remotely without args and show its output.
            # SSHClient.exec_command() returns the tuple (stdin,stdout,stderr)
            stdout = client.exec_command('python3 /tmp/myscript.py')[1]
            print(f"stdout: {stdout}")
            for line in stdout:
                print("1")
                # Process each line in the remote output
                print(line)
            print("here")
            client.close()
            sys.exit(0)
    except IndexError:
        pass

    # No cmd-line args provided, run script normally
    main()