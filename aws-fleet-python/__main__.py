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

# Create a vpc
vpc_name = f"{project_name}-vpc"
vpc = awsx.ec2.Vpc(vpc_name,
    cidr_block=vpc_network_cidr,
    enable_dns_hostnames=True,
    enable_dns_support=True,
    instance_tenancy="default",
    subnet_specs=[
        awsx.ec2.SubnetSpecArgs(
            name=f"{project_name}-public-subnet",
            type=awsx.ec2.SubnetType.PUBLIC,
            cidr_mask=24,
            tags={
                "Name": f"{project_name}-public-subnet",
                "Project": project_name,
            },
        ),
        awsx.ec2.SubnetSpecArgs(
            name=f"{project_name}-private-subnet",
            cidr_mask=24,
            availability_zone=azs.names[0],
            tags={
                "Name": f"{project_name}-private-subnet",
                "Project": project_name,
            },
            map_public_ip_on_launch=False,
        ),
    ],
    tags={
        "Name": vpc_name,
        "Project": project_name,
    })


# vpc = aws.ec2.Vpc(vpc_name,
#     cidr_block=vpc_network_cidr,
#     enable_dns_hostnames=True,
#     enable_dns_support=True,
#     instance_tenancy="default",
#     tags={
#         "Name": vpc_name,
#         "Project": project_name,
#     })

# Create an internet gateway.
igw_name = f"{project_name}-igw"
igw = aws.ec2.InternetGateway(igw_name,
    vpc_id=vpc.id,
    tags={
        "Name": igw_name,
        "Project": project_name,
    })

# Create a route table.
route_table_name = f"{project_name}-route-table"
route_table = aws.ec2.RouteTable(route_table_name,
    vpc_id=vpc.id,
    routes=[
        aws.ec2.RouteTableRouteArgs(cidr_block="0.0.0.0/0", gateway_id=igw.id),
        aws.ec2.RouteTableRouteArgs(cidr_block=vpc.cidr_block, gateway_id="local"),
    ],
    tags={
        "Name": route_table_name,
        "Project": project_name,
    })

# Create a subnet that automatically assigns new instances a public IP address.
public_subnet_name = f"{project_name}-public-subnet"
public_subnet = aws.ec2.Subnet(public_subnet_name,
    vpc_id=vpc.id,
    cidr_block=vpc_network_cidr.split('/')[0] + "/24",
    map_public_ip_on_launch=True,
    availability_zone=azs.names[0],
    tags={
        "Name": public_subnet_name,
        "Project": project_name,
    })

# User data to start a HTTP server in the EC2 instance
# user_data = """#!/bin/bash
# echo "Hello, World from Pulumi!" > index.html
# nohup python -m SimpleHTTPServer 80 &
# """
# with open("user_data.sh", "r") as f:
#     user_data = f.read()

# # Create VPC.
# vpc = aws.ec2.Vpc("vpc",
#     cidr_block=vpc_network_cidr,
#     enable_dns_hostnames=True,
#     enable_dns_support=True)

# # Create an internet gateway.
# gateway = aws.ec2.InternetGateway("gateway", vpc_id=vpc.id)

# # Create a subnet that automatically assigns new instances a public IP address.
# subnet = aws.ec2.Subnet("subnet",
#     vpc_id=vpc.id,
#     cidr_block="10.0.1.0/24",
#     map_public_ip_on_launch=True)

# # Create a route table.
# route_table = aws.ec2.RouteTable("routeTable",
#     vpc_id=vpc.id,
#     routes=[aws.ec2.RouteTableRouteArgs(
#         cidr_block="0.0.0.0/0",
#         gateway_id=gateway.id,
#     )])

# # Associate the route table with the public subnet.
# route_table_association = aws.ec2.RouteTableAssociation("routeTableAssociation",
#     subnet_id=subnet.id,
#     route_table_id=route_table.id)

# # Create a security group allowing inbound access over port 80 and outbound
# # access to anywhere.
# sec_group = aws.ec2.SecurityGroup("secGroup",
#     description="Enable HTTP access",
#     vpc_id=vpc.id,
#     ingress=[aws.ec2.SecurityGroupIngressArgs(
#         from_port=80,
#         to_port=80,
#         protocol="tcp",
#         cidr_blocks=["0.0.0.0/0"],
#     )],
#     egress=[aws.ec2.SecurityGroupEgressArgs(
#         from_port=0,
#         to_port=0,
#         protocol="-1",
#         cidr_blocks=["0.0.0.0/0"],
#     )])

# # Create and launch an EC2 instance into the public subnet.
# server = aws.ec2.Instance("server",
#     instance_type=instance_type,
#     subnet_id=subnet.id,
#     vpc_security_group_ids=[sec_group.id],
#     user_data=user_data,
#     ami=ami,
#     tags={
#         "Name": "webserver",
#     })


# Export the instance's publicly accessible IP address and hostname.
pulumi.export("ami", ami)
# pulumi.export("instance_types", instance_types)
pulumi.export("vpc", vpc_name)

# pulumi.export("ip", server.public_ip)
# pulumi.export("hostname", server.public_dns)
# pulumi.export("url", server.public_dns.apply(lambda public_dns: f"http://{public_dns}"))
