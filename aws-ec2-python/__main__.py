import os
import pulumi
import pulumi_aws_native as aws_native
import pulumi_aws as aws
import pulumi_awsx as awsx
from src.vpc import Vpcx, VpcxArgs
import base64
from json import loads
from random import choice

# Get some configuration values or set default values.
project_name = pulumi.get_project()
aws_region = aws.get_region().name
config = pulumi.Config()
instance_type = config.get("instanceType") if config.get("instanceType") is not None else 'c7gd.8xlarge'
vpc_network_cidr = config.get("vpcNetworkCidr") if config.get("vpcNetworkCidr") is not None else "10.0.0.0/16"
keypair = config.get("keypair") if config.get("keypair") is not None else "jarvis"
useSpotInstance = config.get("useSpotInstance") if config.get("useSpotInstance") is not None else True
ami = config.get("ami") if config.get("ami") is not None else None

scripts_dir = os.path.join(os.path.dirname(__file__), "scripts")
user_data_file = os.path.join(scripts_dir, "user_data.sh")
user_data = (lambda path: base64.b64encode(open(path).read().encode()).decode())(f"{user_data_file}") if os.path.exists(user_data_file) else None

# Create the VPC
vpc = Vpcx(f"{project_name}-vpc", VpcxArgs(
    vpc_cidr_block=vpc_network_cidr,
    aws_region=aws_region,
    sg_ingress_ports=[22],
    tags={
        "Name": f"{project_name}-vpc",
        "Project": project_name,
        "Stack": pulumi.get_stack(),
        "AWS Region": aws_region,
    },
))

if ami is None:
    ami = aws.ec2.get_ami(
        filters=[
            # Look up the latest Amazon Linux 2 AMI ID for the chosen region
            aws.ec2.GetAmiFilterArgs(name="name", values=["amzn2-ami-hvm-*"]),
            # Look up the latest AWS Deep Learning AMI GPU CUDA i.e: ami-0a8da46354e76997e
            # aws.ec2.GetAmiFilterArgs(name="name", values=["AWS Deep Learning*AMI GPU CUDA*"]),
            aws.ec2.GetAmiFilterArgs(name="owner-alias", values=["amazon"]),
        ],
        include_deprecated=False,
        owners=["amazon"],
        most_recent=True).id

# Launch an EC2 instance
instance = aws.ec2.Instance(
    f"{project_name}-instance",
    ami=ami,
    availability_zone=choice(aws.get_availability_zones().names),
    instance_type=instance_type,
    subnet_id=vpc.vpc.public_subnet_ids.apply(lambda ids: choice(ids)),
    vpc_security_group_ids=[vpc.security_group.id],
    key_name=keypair,
    user_data=user_data,
    tags={
        "Name": f"{project_name}-instance",
        "Project": project_name,
        "Stack": pulumi.get_stack(),
        "AWS Region": aws_region,
    },
)

pulumi.export("vpc_id", vpc.vpc.vpc_id)
pulumi.export("vpc_private_subnet_ids", vpc.vpc.private_subnet_ids)
pulumi.export("vpc_public_subnet_ids", vpc.vpc.public_subnet_ids)
pulumi.export("vpc_security_group_id", vpc.security_group.id)
pulumi.export("ami", ami)
pulumi.export("public_dns", instance.public_dns)
pulumi.export("public_ip", instance.public_ip)
