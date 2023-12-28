import pulumi
import pulumi_aws as aws
import pulumi_awsx as awsx
from datetime import datetime

# Get some configuration values or set default values.
dir_name = pulumi.get_project()
project_name = "aws-graphstorm"
config = pulumi.Config()
instance_types = config.get("instanceTypes") if config.get("instanceTypes") is not None else ['t3.micro', 't4g.small']
vpc_network_cidr = config.get("vpcNetworkCidr") if config.get("vpcNetworkCidr") is not None else "10.0.0.0/16"
keypair = config.get("keypair") if config.get("keypair") is not None else "jarvis"

# Look up the latest AWS Deep Learning AMI GPU CUDA i.e: ami-0a8da46354e76997e
ami = aws.ec2.get_ami(
    filters=[
        aws.ec2.GetAmiFilterArgs(name="name", values=["AWS Deep Learning*AMI GPU CUDA*"]),
        aws.ec2.GetAmiFilterArgs(name="owner-alias", values=["amazon"]),
    ],
    include_deprecated=False,
    owners=["amazon"],
    most_recent=True).id

# Get all availability zones
azs = aws.get_availability_zones(state="available")

# Create a vpc https://www.pulumi.com/docs/clouds/aws/guides/vpc/
vpc_name = f"{project_name}-vpc"
vpc = awsx.ec2.Vpc(vpc_name, awsx.ec2.VpcArgs(
    cidr_block=vpc_network_cidr,
    number_of_availability_zones=len(azs.names),
    subnet_specs=[
        awsx.ec2.SubnetSpecArgs(
            type=awsx.ec2.SubnetType.PUBLIC,
            cidr_mask=22,
        ),
        awsx.ec2.SubnetSpecArgs(
            type=awsx.ec2.SubnetType.PRIVATE,
            cidr_mask=22,
        ),
    ],
    nat_gateways=awsx.ec2.NatGatewayConfigurationArgs(
        strategy=awsx.ec2.NatGatewayStrategy.NONE,
    ),
    subnet_strategy=awsx.ec2.SubnetAllocationStrategy.AUTO,
    tags={
        "Name": vpc_name,
        "Project": project_name,
    }
))

# user_data = """#!/bin/bash
# echo "Hello, World from Pulumi!" > index.html
# nohup python -m SimpleHTTPServer 80 &
# """
# User data to start a HTTP server in the EC2 instance
with open(f"user_data.sh", "r") as f:
    user_data = f.read()

# Create a security group allowing inbound access over port 22 and 443 (https) and outbound access to anywhere.
security_group_name = f"{project_name}-security-group"
security_group = aws.ec2.SecurityGroup(
    security_group_name,
    vpc_id=vpc.vpc_id,
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            from_port=22,
            to_port=22,
            protocol="tcp",
            cidr_blocks=["0.0.0.0/0"],
        ),
    ],
    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            from_port=0,
            to_port=0,
            protocol="-1",
            cidr_blocks=["0.0.0.0/0"],
        )
    ],
    tags={
        "Name": security_group_name,
        "Project": project_name,
    }
)

# Create and launch an EC2 instance into the public subnet.
instance_name = f"{project_name}-instance"
instance = aws.ec2.Instance(
    instance_name,
    instance_type=instance_type,
    subnet_id=subnet.id,
    vpc_security_group_ids=[security_group.id],
    user_data=user_data,
    ami=ami,
    tags={
        "Name": instance_name,
        "Project": project_name,
    }
)

# Export the instance's publicly accessible IP address and hostname.
pulumi.export("ami", ami)
# pulumi.export("instance_types", instance_types)
pulumi.export("vpc", vpc_name)

# pulumi.export("ip", server.public_ip)
# pulumi.export("hostname", server.public_dns)
# pulumi.export("url", server.public_dns.apply(lambda public_dns: f"http://{public_dns}"))

[r5n.large, r4.large, r5dn.large, i4i.large, i3.large, m7i-flex.large, m7i.large, r5ad.large, r5d.large c5a.large, c5d.large, c5n.large, inf1.xlarge]