import pulumi
import pulumi_aws_native as aws_native
import pulumi_aws as aws
import pulumi_awsx as awsx
import base64
from json import loads

# Get some configuration values or set default values.
project_name = pulumi.get_project()
aws_region = aws.get_region().name
config = pulumi.Config()
instance_type = config.get("instanceType") if config.get("instanceType") is not None else 'c7gd.8xlarge'
vpc_network_cidr = config.get("vpcNetworkCidr") if config.get("vpcNetworkCidr") is not None else "10.0.0.0/16"
keypair = config.get("keypair") if config.get("keypair") is not None else "jarvis"


# Create the VPC
vpc = aws_native.ec2.Vpc("my-vpc",
    cidr_block="10.0.0.0/16",
    enable_dns_support=True,
    enable_dns_hostnames=True,
    tags=[{
        "key": "Name",
        "value": "my-vpc"
    }])

# Create a subnet
subnet = aws_native.ec2.Subnet("my-subnet",
    vpc_id=vpc.id,
    cidr_block="10.0.1.0/24",
    availability_zone="us-west-2a",
    map_public_ip_on_launch=True,
    tags=[{
        "key": "Name",
        "value": "my-subnet"
    }])

# Create an internet gateway
gateway = aws_native.ec2.InternetGateway("my-gateway",
    vpc_id=vpc.id)

# Create a route table
route_table = aws_native.ec2.RouteTable("my-route-table",
    vpc_id=vpc.id,
    routes=[{
        "destination_cidr_block": "0.0.0.0/0",
        "gateway_id": gateway.id
    }],
    tags=[{
        "key": "Name",
        "value": "my-route-table"
    }])

# Associate the route table with the subnet
route_table_association = aws_native.ec2.RouteTableAssociation("my-route-table-association",
    subnet_id=subnet.id,
    route_table_id=route_table.id)

# Create a security group
security_group = aws_native.ec2.SecurityGroup("web-secgrp",
    vpc_id=vpc.id,
    group_description="Enable HTTP access",
    security_group_ingress=[{
        "ip_protocol": "tcp",
        "from_port": 80,
        "to_port": 80,
        "cidr_ip": "0.0.0.0/0"
    }],
    tags=[{
        "key": "Name",
        "value": "web-secgrp"
    }])

# Create a key pair
key_pair = aws_native.ec2.KeyPair("jarvis-key",
    key_name="jarvis")

# Launch an EC2 instance
instance = aws_native.ec2.Instance("web-server-www",
    instance_type=pulumi.Config('aws').require('instanceType'),
    subnet_id=subnet.id,
    key_name=key_pair.key_name,
    security_group_ids=[security_group.id],
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