import pulumi
import pulumi_aws as aws
import pulumi_awsx as awsx
import base64
from json import loads

# Get some configuration values or set default values.
dir_name = pulumi.get_project()
aws_region = aws.get_region().name
project_name = "hack-lab"
config = pulumi.Config()
vpc_network_cidr = config.get("vpcNetworkCidr") if config.get("vpcNetworkCidr") is not None else "10.0.0.0/16"
keypair = config.get("keypair") if config.get("keypair") is not None else "jarvis"

user_data_file = f"user_data.sh"

# Look up the latest Kali Linux i.e: ami-094d83ad9850c1a43
ami = aws.ec2.get_ami(
    filters=[
        aws.ec2.GetAmiFilterArgs(name="name", values=["AWS Deep Learning*AMI GPU CUDA*"]),
        aws.ec2.GetAmiFilterArgs(name="owner-alias", values=["amazon"]),
    ],
    include_deprecated=False,
    owners=["aws-marketplace"],
    most_recent=True).id

# Get all availability zones
azs = aws.get_availability_zones(state="available")
