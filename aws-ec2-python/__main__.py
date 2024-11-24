import os
import pulumi
import pulumi_aws_native as aws_native
import pulumi_aws as aws
import pulumi_awsx as awsx
from src.vpc import Vpcx, VpcxArgs
import base64
from json import loads

# Get some configuration values or set default values.
project_name = pulumi.get_project()
aws_region = aws.get_region().name
config = pulumi.Config()
instance_type = config.get("instanceType") if config.get("instanceType") is not None else 'c7gd.8xlarge'
vpc_network_cidr = config.get("vpcNetworkCidr") if config.get("vpcNetworkCidr") is not None else "10.0.0.0/16"
keypair = config.get("keypair") if config.get("keypair") is not None else "jarvis"

scripts_dir = os.path.join(os.path.dirname(__file__), "scripts")
user_data_file = os.path.join(scripts_dir, f"user_data.sh")

# Create the VPC
vpc = Vpcx(f"{project_name}-vpc", VpcxArgs(
    vpc_cidr_block=vpc_network_cidr,
    azs=aws.get_availability_zones().names,
    aws_region=aws_region,
    sg_ingress_ports=[22],
    tags={
        "Project": project_name,
        "Stack": pulumi.get_stack(),
        "AWS Region": aws_region,
    },
))

# Look up the latest AWS Deep Learning AMI GPU CUDA i.e: ami-0a8da46354e76997e
ami = aws.ec2.get_ami(
    filters=[
        aws.ec2.GetAmiFilterArgs(name="name", values=["AWS Deep Learning*AMI GPU CUDA*"]),
        aws.ec2.GetAmiFilterArgs(name="owner-alias", values=["amazon"]),
    ],
    include_deprecated=False,
    owners=["amazon"],
    most_recent=True).id

# Launch an EC2 instance
ec2_instance = aws.ec2.Instance(
    f"{project_name}-instance",
    ami=ami,  # Example Amazon Linux 2 AMI ID for the chosen region
    instance_type=instance_type,
    subnet_id=vpc.vpc.public_subnet_ids[0],
    vpc_security_group_ids=[vpc.security_group.id],
    tags={"Name": f"{project_name}-instance"},
)

server = aws.ec2.Instance("web-server-www",
    instance_type=instance_type,
    key_name=keypair,
    ami="ami-0c55b159cbfafe1f0",  # Update this AMI as needed
    vpc_security_group_ids=[vpc.security_group.id],
    subnet_id=vpc.public_subnet_ids[0],
    user_data=base64.b64encode(open(user_data_file, "rb").read()).decode("ascii"),
    tags={
        "Name": "web-server-www",
    })


instance = aws_native.ec2.Instance("web-server-www",
    instance_type=instance_type,
    key_name=keypair,
    ami="ami-0c55b159cbfafe1f0",  # Update this AMI as needed
    tags=[{
        "key": "Name",
        "value": "web-server-www"
    }])

# Create an EBS volume
ebs_volume = aws_native.ec2.Volume("my-ebs-volume",
    availability_zone="us-west-2a",
    size=8,  # Size in GiB
    tags=[{
        "key": "Name",
        "value": "my-ebs-volume"
    }])

# Attach the EBS volume to the instance
volume_attachment = aws_native.ec2.VolumeAttachment("my-volume-attachment",
    device="/dev/sdh",
    instance_id=instance.id,
    volume_id=ebs_volume.id)

# Export the instance's public DNS
pulumi.export("public_dns", instance.public_dns_name)