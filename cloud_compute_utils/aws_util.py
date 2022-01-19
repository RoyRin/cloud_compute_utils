import sys
import boto3
import botocore

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


def get_s3_client(region=AWS_REGION):
    return boto3.resource('s3', region_name=region)


## EC2 stuff
def get_attached_volumes(instance):
    return [vol for vol in instance.volumes.all()]


def print_instance(instance):
    total_size = sum(vol.size for vol in get_attached_volumes(instance))
    print(
        f"{instance.id}, {instance.public_dns_name} : {instance.state['Name']} ({total_size} GB)"
    )


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


def terminate_instance(instance):
    try:
        instance.stop()
        instance.terminate()
        print(f"terminated {instance.id}")
    except Exception as e:
        print(f"skipping instance {instance.id} - {instance.state['Name']}")
        # print(e)


def terminate_all_instances(ec2, keypair_name=None):
    if keypair_name is None:
        instances = get_ec2_instances(ec2)
    else:
        instances = get_instances_with_keypair(ec2, keypair_name)
    for instance in instances:
        if instance.state['Name'] == 'terminated':
            continue
        terminate_instance(instance)


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


def get_bucket(s3, bucket_name):
    """get bucket

    Args:
        s3 ([type]): [description]
        bucket_name ([type]): [description]

    Returns:
        (s3.bucket, bool): bucket, if-it-exists
    """
    bucket = s3.Bucket(bucket_name)
    exists = True
    try:
        s3.meta.client.head_bucket(Bucket='mybucket')
    except botocore.exceptions.ClientError as e:
        # If a client error is thrown, then check that it was a 404 error.
        # If it was a 404 error, then the bucket does not exist.
        error_code = e.response['Error']['Code']
        if error_code == '404':
            exists = False
    return bucket, exists


def get_bucket_names(s3):
    """get a list of available bucket names

    Args:
        s3 ([]): boto s3.client

    Returns:
        [list]: list of strings
    """
    return [bucket.name for bucket in s3.buckets.all()]


def write_file_to_bucket(*, s3, bucket_name, remote_filepath, local_filepath):
    """write a file to a bucket"""
    s3.Object(bucket_name,
              remote_filepath).put(Body=open(local_filepath, 'rb'))


def download_file_from_bucket(s3, bucket_name, remote_filepath,
                              local_filepath):
    """download a file from a bucket"""

    try:
        s3.Bucket(bucket_name).download_file(remote_filepath, local_filepath)
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
