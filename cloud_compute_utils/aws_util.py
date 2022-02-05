import sys
import boto3
import botocore
import os

AWS_REGION = "us-east-1"
#DEFAULT_AMI = "ami-08e4e35cccc6189f4" - FEDORA
DEFAULT_AMI = "ami-04505e74c0741db8d"  # ubuntu


def get_ec2_client(region=AWS_REGION):
    """get EC2 client

    Returns:
        [type]: client
    """
    ec2 = boto3.resource('ec2', region_name=region)
    return ec2


def get_s3_resource(region=AWS_REGION):
    return boto3.resource('s3', region_name=region)


def get_s3_client(region=AWS_REGION):
    return boto3.client('s3', region_name=region)


## EC2 stuff
def get_attached_volumes(instance):
    return [vol for vol in instance.volumes.all()]


def instance_str(instance):
    total_size = sum(vol.size for vol in get_attached_volumes(instance))
    return (
        f"{instance.id}, {instance.public_dns_name} : {instance.state['Name']} ({total_size} GB)"
    )


def print_instance(instance):
    print(instance_str(instance))


def get_ec2_instances(ec2):
    """get EC2 instances

    Args:
        ec2 ([type]): client

    Returns:
        [type]: list of ec2 instances
    """
    instances = [instance for instance in ec2.instances.all()]
    return instances


def filtered_ec2s(ec2, filter_function):

    instances = get_ec2_instances(ec2)
    filtered_instances = [
        instance for instance in instances if filter_function(instance)
    ]
    return filtered_instances


def is_running(instance):
    return instance.state['Name'] == 'running'


def get_running_instances(ec2):
    return filtered_ec2s(ec2, is_running)


def stop_instance(instance, verbose=False):
    try:
        instance.stop()
        if verbose:
            print(f"Stop {instance.id}")
    except Exception as e:
        print(f"skipping instance {instance.id} - {instance.state['Name']}")
        print(e)


def terminate_instance(instance, verbose=False):
    stop_instance(instance, verbose=verbose)
    try:
        instance.terminate()
        if verbose:
            print(f"terminated {instance.id}")
    except Exception as e:
        print(f"skipping instance {instance.id} - {instance.state['Name']}")
        # print(e)


def do_x_all_instances_with_keypair(
        ec2,
        keypair_name,
        instance_ids=None,
        action=None,  # function of the form: func(instance, verbose=False)
        dry_run=True,
        verbose=False):
    if dry_run:
        print("dry run")
    instances = get_instances_with_keypair(ec2, keypair_name)
    if instance_ids is not None and len(instance_ids) > 0:
        # if instance_ids provided, only include those
        instances = [
            instance for instance in instances if instance.id in instance_ids
        ]
    for instance in instances:
        if instance.state['Name'] == 'terminated':
            continue
        if dry_run:
            print(f"would act on {instance.id} - {instance_str(instance)}")
            continue

        action(instance, verbose=verbose)
        if verbose:
            print_instance(instance)


def terminate_all_instances_with_keypair(ec2,
                                         keypair_name,
                                         instance_ids=None,
                                         dry_run=True,
                                         verbose=False):
    do_x_all_instances_with_keypair(ec2,
                                    keypair_name=keypair_name,
                                    instance_ids=instance_ids,
                                    action=terminate_instance,
                                    dry_run=dry_run,
                                    verbose=verbose)


def stop_all_instances_with_keypair(ec2,
                                    keypair_name,
                                    instance_ids=None,
                                    dry_run=True,
                                    verbose=False):
    do_x_all_instances_with_keypair(ec2,
                                    keypair_name=keypair_name,
                                    instance_ids=instance_ids,
                                    action=stop_instance,
                                    dry_run=dry_run,
                                    verbose=verbose)


def create_instances(*,
                     ec2,
                     image_id,
                     minCount=1,
                     maxCount=1,
                     keypair_name="",
                     instance_type,
                     security_group_ids=None,
                     size=10,
                     device_name="/dev/sda1"):
    image_id = image_id or DEFAULT_AMI
    security_group_ids_ = security_group_ids or []
    instance_type = instance_type or "t2.micro"
    print(f"{image_id} {instance_type} {security_group_ids_} - size : {size}")

    instances = ec2.create_instances(
        ImageId=image_id,
        MinCount=minCount,
        MaxCount=maxCount,
        InstanceType=instance_type,
        KeyName=keypair_name,
        SecurityGroupIds=security_group_ids_,  #security_group_ids
        BlockDeviceMappings=[{
            'DeviceName': device_name,
            'Ebs': {
                'VolumeSize': size,
                'VolumeType': 'standard'
            }
        }])
    return instances


### S3 stuff


def get_bucket(s3_resource, bucket_name):
    """get bucket

    Args:
        s3 ([type]): [description]
        bucket_name ([type]): [description]

    Returns:
        (s3.bucket, bool): bucket, if-it-exists
    """
    bucket = s3_resource.Bucket(bucket_name)
    exists = True
    try:
        s3_resource.meta.client.head_bucket(Bucket='mybucket')
    except botocore.exceptions.ClientError as e:
        # If a client error is thrown, then check that it was a 404 error.
        # If it was a 404 error, then the bucket does not exist.
        error_code = e.response['Error']['Code']
        if error_code == '404':
            exists = False
    return bucket, exists


def get_bucket_names(s3_resource):
    """get a list of available bucket names

    Args:
        s3 ([]): boto s3.client

    Returns:
        [list]: list of strings
    """
    return [bucket.name for bucket in s3_resource.buckets.all()]


def upload_file(s3_client, file_name, bucket, object_name=None):
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """

    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = os.path.basename(file_name)

    try:
        response = s3_client.upload_file(file_name, bucket, object_name)
    except botocore.exceptions.ClientError as e:
        print(e)
        return False
    return True


def download_file_from_bucket(s3_client, bucket_name, remote_filepath,
                              local_filepath):
    """download a file from a bucket"""

    try:
        s3.download_file(bucket_name, remote_filepath, local_filepath)
        #s3_client.Bucket(bucket_name).download_file(remote_filepath,
        #                                            local_filepath)
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "404":
            print("The object does not exist.")
        else:
            raise


## Security Group stuff
def get_instances_with_keypair(ec2, keypair_name):
    return filtered_ec2s(ec2,
                         lambda instance: instance.key_name == keypair_name)


def print_security_group(security_group):
    print(f"{security_group.id} : {security_group.group_name}")


def get_security_groups(ec2):
    return ec2.security_groups.all()


def create_security_group(ec2, vpc_id, group_name="allow-inbound-ssh"):
    """Create security group

    Args:
        ec2 ([type]): [description]
        vpc_id ([type]): [description]

    Returns:
        [type]: [description]
    """
    security_group = ec2.create_security_group(
        Description='Allow inbound SSH traffic',
        GroupName=group_name,
        VpcId=vpc_id,
        TagSpecifications=[
            {
                'ResourceType': 'security-group',
                'Tags': [
                    {
                        'Key': 'Name',
                        'Value': 'allow-inbound-ssh'
                    },
                ]
            },
        ],
    )

    security_group.authorize_ingress(
        CidrIp='0.0.0.0/0',
        FromPort=22,
        ToPort=22,
        IpProtocol='tcp',
    )
    return security_group
