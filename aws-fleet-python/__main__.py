import pulumi
import pulumi_aws as aws
import pulumi_awsx as awsx
import base64
from datetime import datetime, timedelta

# Get some configuration values or set default values.
dir_name = pulumi.get_project()
project_name = "aws-graphstorm"
config = pulumi.Config()
instance_types = config.get("instanceTypes") if config.get("instanceTypes") is not None else ['t3.micro', 't4g.small']
vpc_network_cidr = config.get("vpcNetworkCidr") if config.get("vpcNetworkCidr") is not None else "10.0.0.0/16"
keypair = config.get("keypair") if config.get("keypair") is not None else "jarvis"

valid_until = datetime.now() + timedelta(days=365) # 1 year from now
user_data_file = f"user_data.sh"

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
# with open(f"user_data.sh", "r") as f:
#     user_data = f.read()

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

# Define the EBS block device mappings
block_device_mappings = [
    aws.ec2.LaunchTemplateBlockDeviceMappingArgs(
        device_name="/dev/sda1",
        ebs=aws.ec2.LaunchTemplateBlockDeviceMappingEbsArgs(
            delete_on_termination=True,
            iops=3000,
            snapshot_id="snap-01c7cdb5e9eaf8fde",
            volume_size=100,
            volume_type="gp3",
            throughput=125,
            encrypted=False
        ),
    ),
    aws.ec2.LaunchTemplateBlockDeviceMappingArgs(
        device_name="/dev/sdb",
        virtual_name="ephemeral0",
        ebs=aws.ec2.LaunchTemplateBlockDeviceMappingEbsArgs(
            delete_on_termination=True,
            volume_size=10,
            iops=3000,
            volume_type="gp3",
            throughput=125,
            encrypted=False
        ),
    ),
    aws.ec2.LaunchTemplateBlockDeviceMappingArgs(
        device_name="/dev/sdc",
        virtual_name="ephemeral1",
        ebs=aws.ec2.LaunchTemplateBlockDeviceMappingEbsArgs(
            delete_on_termination=True,
            volume_size=10,
            iops=3000,
            volume_type="gp3",
            throughput=125,
            encrypted=False
        ),
    )
]

# Launch template for the spot fleet
launch_template_name = f"{project_name}-launch-template"
launch_template = aws.ec2.LaunchTemplate(
    launch_template_name,
    block_device_mappings=block_device_mappings,
    image_id=ami,
    key_name=keypair,
    instance_market_options=aws.ec2.LaunchTemplateInstanceMarketOptionsArgs(
        market_type="spot",
        spot_options=aws.ec2.LaunchTemplateInstanceMarketOptionsSpotOptionsArgs(
            instance_interruption_behavior="terminate",
            max_price="0.04",
            spot_instance_type="persistent",
            valid_until=valid_until.strftime("%Y-%m-%dT%H:%M:%SZ"),
            ),
        ),
    instance_type="c5.large",
    vpc_security_group_ids=[security_group.id],
    user_data=(lambda path: base64.b64encode(open(path).read().encode()).decode())(f"{user_data_file}"),
    tags={
        "Name": launch_template_name,
        "Project": project_name,
    }
)

auto_scaling_group_name = f"{project_name}-auto-scaling-group"
auto_scaling_group = aws.autoscaling.Group(
    auto_scaling_group_name,
    availability_zones=["us-east-1a"],
    desired_capacity=1,
    max_size=1,
    min_size=1,
    mixed_instances_policy=aws.autoscaling.GroupMixedInstancesPolicyArgs(
        launch_template=aws.autoscaling.GroupMixedInstancesPolicyLaunchTemplateArgs(
            launch_template_specification=aws.autoscaling.GroupMixedInstancesPolicyLaunchTemplateLaunchTemplateSpecificationArgs(
                launch_template_id=example_launch_template.id,
            ),
            overrides=[
                aws.autoscaling.GroupMixedInstancesPolicyLaunchTemplateOverrideArgs(
                    instance_type="c4.large",
                    weighted_capacity="3",
                ),
                aws.autoscaling.GroupMixedInstancesPolicyLaunchTemplateOverrideArgs(
                    instance_type="c3.large",
                    weighted_capacity="2",
                ),
            ],
        ),
    ))

# Export the instance's publicly accessible IP address and hostname.
pulumi.export("ami", ami)
# pulumi.export("instance_types", instance_types)
pulumi.export("vpc", vpc_name)

# pulumi.export("ip", server.public_ip)
# pulumi.export("hostname", server.public_dns)
# pulumi.export("url", server.public_dns.apply(lambda public_dns: f"http://{public_dns}"))
