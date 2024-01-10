import pulumi
import pulumi_aws as aws
import pulumi_awsx as awsx
from vpc import Vpcx, VpcxArgs
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
        aws.ec2.GetAmiFilterArgs(name="name", values=["kali-last-snapshot-*"]),
        aws.ec2.GetAmiFilterArgs(name="owner-alias", values=["aws-marketplace"]),
    ],
    include_deprecated=False,
    owners=["679593333241"], # kali linux marketplace owner id
    most_recent=True).id

# Get all availability zones
azs = aws.get_availability_zones(state="available")

# Create a VPC with a size /16 CIDR block
vpc = Vpcx(
    project_name,
    VpcxArgs(
        cidr_block=vpc_network_cidr,
        enable_dns_hostnames=True,
        enable_dns_support=True,
        tags={
            "Name": f"{project_name}-vpc",
            "Project": project_name,
            "Owner": "Jarvis",
            "Environment": "Hack-Lab",
        },
    ),
)

# Export the instance's publicly accessible IP address and hostname.
pulumi.export("vpc_network_cidr", vpc_network_cidr)
pulumi.export("aws_region", aws_region)
pulumi.export("ami", ami)
pulumi.export("azs", azs.names)