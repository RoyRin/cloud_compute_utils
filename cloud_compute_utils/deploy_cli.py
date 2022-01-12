from typing_extensions import Required
from deployments import aws_util
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


@click.group(help=""" """)
@click.pass_context
def cli(ctx):
    return


@cli.command(name="spin-up-ec2", help=""" Spin up EC2 instance(s) """)
@click.option("--N", '-N', default=1, help='number of instances')
@click.option('--keypair-name', "-k", default="", help='name of keypair')
@click.option('--image-id',
              "-i",
              default="ami-08e4e35cccc6189f4",
              help='image id')
@click.option('--security-group-ids',
              "-s",
              multiple=True,
              required=True,
              help='security group id (multiple allowed, `-s ## -s ##` )')
@click.pass_context
def spin_up_ec2(ctx, n, keypair_name, image_id, security_group_ids):
    ec2 = aws_util.get_ec2_client()
    security_group_ids = list(security_group_ids)
    instances = aws_util.create_instances(
        ec2,
        image_id=image_id,
        minCount=n,
        maxCount=n,
        keypair_name=keypair_name,
        security_group_ids=security_group_ids)
    for instance in instances:
        aws_util.print_instance(instance)


@cli.command(
    name="create-ec2-security-group",
    help="""Create a security group that can be accessed from anywhere""")
@click.option('--vpc-id', "-v", required=True, help='name of keypair')
@click.option('--group-name', "-g", help='name of security group name')
@click.pass_context
def create_ec2_security_group(ctx, vpc_id, group_name):
    ec2 = aws_util.get_ec2_client()
    security_group = aws_util.create_security_group(ec2=ec2,
                                                    vpc_id=vpc_id,
                                                    group_name=group_name)
    print(security_group.id)


@cli.command(name="list-security-groups",
             help=""" Lists all security groups""")
@click.pass_context
def list_security_groups(ctx):
    ec2 = aws_util.get_ec2_client()
    for sg in aws_util.get_security_groups(ec2):
        aws_util.print_security_group(sg)


@cli.command(
    name="list-ec2",
    help=
    """ Lists all non-terminated instances (optionally: associated with a specific keypair)"""
)
@click.option('--keypair-name', "-k", default=None, help='name of keypair')
@click.pass_context
def list_ec2(ctx, keypair_name):
    ec2 = aws_util.get_ec2_client()
    if keypair_name is not None:
        instances = aws_util.get_instances_with_keypair(ec2, keypair_name)
    else:
        instances = aws_util.get_ec2_instances(ec2)
    for instance in instances:
        if instance.state['Name'] == 'terminated':
            continue
        aws_util.print_instance(instance)


@cli.command(
    name="spin-down-ec2",
    help=""" Spins down all instances associated with a specific keypair """)
@click.option(
    '--keypair-name',
    "-k",
    default=None,
    help='name of keypair (if not provided, this will spin down all instances)'
)
@click.pass_context
def spin_down_ec2(ctx, keypair_name):
    ec2 = aws_util.get_ec2_client()
    # get instances
    if keypair_name is None:
        instances = aws_util.get_ec2_instances(ec2)
    else:
        instances = aws_util.get_instances_with_keypair(ec2, keypair_name)
    # terminate instances
    for instance in instances:
        if instance.state['Name'] == 'terminated':
            continue
        aws_util.terminate_instance(instance)


def main():
    cli()


if __name__ == "__main__":
    main()
