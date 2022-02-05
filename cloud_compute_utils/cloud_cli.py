from typing_extensions import Required
from cloud_compute_utils import aws_util
import click
import logging
import os

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
format = "%(asctime)s - %(levelname)s - %(message)s"
format = "%(levelname)s - %(message)s"
stream_handler.setFormatter(
    logging.Formatter(format, datefmt="%Y-%m-%d %H:%M:%S"))

logging.basicConfig(level=logging.INFO, handlers=[stream_handler])
logger = logging.getLogger()
AWS_REGION = "us-east-1"


@click.group(help=""" """)
@click.pass_context
def cli(ctx):
    return


@cli.command(name="spin-up-ec2", help=""" Spin up EC2 instance(s) """)
@click.option("--instance-number", '-N', default=1, help='number of instances')
@click.option('--keypair-name', "-k", default="", help='name of keypair')
@click.option('--image-id', "-i", help='image id')
@click.option('--instance-type', "-t", help='instance_type')
@click.option('--security-group-ids',
              "-g",
              multiple=True,
              required=True,
              help='security group id (multiple allowed, `-s ## -s ##` )')
@click.option('--size', "-s", default=10, help='size of instance')
@click.option('--region',
              "-r",
              default=AWS_REGION,
              show_default=True,
              help='AWS region')
@click.pass_context
def spin_up_ec2(ctx, instance_number, keypair_name, image_id, instance_type,
                security_group_ids, size, region):
    ec2 = aws_util.get_ec2_client(region=region)
    security_group_ids = list(security_group_ids)
    instances = aws_util.create_instances(
        ec2=ec2,
        image_id=image_id,
        minCount=instance_number,
        maxCount=instance_number,
        keypair_name=keypair_name,
        instance_type=instance_type,
        security_group_ids=security_group_ids,
        size=size)
    for instance in instances:
        aws_util.print_instance(instance)


@cli.command(
    name="create-ec2-security-group",
    help="""Create a security group that can be accessed from anywhere""")
@click.option('--vpc-id', "-v", required=True, help='name of keypair')
@click.option('--group-name', "-g", help='name of security group name')
@click.option('--region',
              "-r",
              default=AWS_REGION,
              show_default=True,
              help='AWS region')
@click.pass_context
def create_ec2_security_group(ctx, vpc_id, group_name, region):
    ec2 = aws_util.get_ec2_client(region=region)
    security_group = aws_util.create_security_group(ec2=ec2,
                                                    vpc_id=vpc_id,
                                                    group_name=group_name)
    print(security_group.id)


@cli.command(name="list-security-groups",
             help=""" Lists all security groups""")
@click.option('--region',
              "-r",
              default=AWS_REGION,
              show_default=True,
              help='AWS region')
@click.pass_context
def list_security_groups(ctx, region):
    ec2 = aws_util.get_ec2_client(region=region)
    for sg in aws_util.get_security_groups(ec2):
        aws_util.print_security_group(sg)


@cli.command(
    name="list-ec2",
    help=
    """ Lists all non-terminated instances (optionally: associated with a specific keypair)"""
)
@click.option('--keypair-name', "-k", default=None, help='name of keypair')
@click.option('--region',
              "-r",
              default=AWS_REGION,
              show_default=True,
              help='AWS region')
@click.pass_context
def list_ec2(ctx, keypair_name, region):
    ec2 = aws_util.get_ec2_client(region=region)
    if keypair_name is not None:
        instances = aws_util.get_instances_with_keypair(ec2, keypair_name)
    else:
        instances = aws_util.get_ec2_instances(ec2)
    for instance in instances:
        if instance.state['Name'] == 'terminated':
            continue
        aws_util.print_instance(instance)


@cli.command(
    name="terminate-ec2",
    help="""Terminates all instances associated with a specific keypair """)
@click.option(
    '--keypair-name',
    "-k",
    required=True,
    help=
    'name of keypair instance created with (will spin down all keypair names if not specified)'
)
@click.option(
    '--instance-ids',
    "-i",
    multiple=True,
    help='name of instances (if not provided, this will spin down all instances)'
)
@click.option('--region',
              "-r",
              default=AWS_REGION,
              show_default=True,
              help='AWS region')
@click.option("--dry-run", "-d", is_flag=True, help="dry run")
@click.pass_context
def terminate_ec2(ctx, keypair_name, instance_ids, region, dry_run):
    ec2 = aws_util.get_ec2_client(region=region)
    # get instances
    aws_util.terminate_all_instances_with_keypair(ec2,
                                                  keypair_name,
                                                  instance_ids=instance_ids,
                                                  dry_run=dry_run,
                                                  verbose=True)


@cli.command(name="stop-ec2",
             help="""Stops all instances associated with a specific keypair """
             )
@click.option(
    '--keypair-name',
    "-k",
    required=True,
    help=
    'name of keypair instance created with (will spin down all keypair names if not specified)'
)
@click.option(
    '--instance-ids',
    "-i",
    multiple=True,
    help='name of instances (if not provided, this will spin down all instances)'
)
@click.option('--region',
              "-r",
              default=AWS_REGION,
              show_default=True,
              help='AWS region')
@click.option("--dry-run", "-d", is_flag=True, help="dry run")
@click.pass_context
def stop_ec2(ctx, keypair_name, instance_ids, region, dry_run):
    ec2 = aws_util.get_ec2_client(region=region)
    # get instances
    aws_util.stop_all_instances_with_keypair(ec2,
                                             keypair_name,
                                             instance_ids=instance_ids,
                                             dry_run=dry_run,
                                             verbose=True)


def main():
    cli()


if __name__ == "__main__":
    main()
