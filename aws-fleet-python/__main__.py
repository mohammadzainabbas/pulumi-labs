import pulumi
import pulumi_aws as aws
import pulumi_awsx as awsx
import base64
from datetime import datetime, timedelta
from json import loads

# Get some configuration values or set default values.
dir_name = pulumi.get_project()
aws_region = aws.get_region().name
project_name = "aws-graphstorm"
config = pulumi.Config()
instance_types = config.get("instanceTypes") if config.get("instanceTypes") is not None else ['t3.micro', 't4g.small']
vpc_network_cidr = config.get("vpcNetworkCidr") if config.get("vpcNetworkCidr") is not None else "10.0.0.0/16"
keypair = config.get("keypair") if config.get("keypair") is not None else "jarvis"

valid_until = datetime.now() + timedelta(days=365) # 1 year from now
user_data_file = f"user_data.sh"
instance_types = loads(instance_types) if isinstance(instance_types, str) else instance_types



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
        aws.ec2.SecurityGroupIngressArgs(
            from_port=80,
            to_port=80,
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

# Create a static IP address for the instance.
elastic_ip = aws.ec2.Eip(f"{project_name}-elastic-ip", vpc=True)

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

def process_user_data():
    with open(user_data_file, "r") as f:
        lines = f.readlines()
    lines = [line.replace("{{AWS_REGION}}", aws_region) for line in lines]
    lines = [line.replace("{{VALID_UNTIL}}", valid_until.strftime("%Y-%m-%dT%H:%M:%SZ")) for line in lines]
    lines = [line.replace("{{INSTANCE_TYPES}}", str(instance_types)) for line in lines]
    with open(user_data_file, "w") as f:
        f.writelines(lines)

# Launch template for the spot fleet
launch_template_name = f"{project_name}-launch-template"
launch_template = aws.ec2.LaunchTemplate(
    launch_template_name,
    block_device_mappings=block_device_mappings,
    image_id=ami,
    key_name=keypair,
    instance_type="c5.large",
    vpc_security_group_ids=[security_group.id],
    update_default_version=True,
    user_data=(lambda path: base64.b64encode(open(path).read().encode()).decode())(f"{user_data_file}"),
    tags={
        "Name": launch_template_name,
        "Project": project_name,
    }
)

# Override the instance type for the spot fleet
auto_scaling_group_overrides = []
for instance_type in instance_types:
    auto_scaling_group_overrides.append(
        aws.autoscaling.GroupMixedInstancesPolicyLaunchTemplateOverrideArgs(    
            instance_type=instance_type,
            weighted_capacity="1",
        )
    )

# Create an auto scaling group with the launch template
auto_scaling_group_name = f"{project_name}-auto-scaling-group"
auto_scaling_group = aws.autoscaling.Group(
    auto_scaling_group_name,
    desired_capacity=1,
    max_size=1,
    min_size=1,
    mixed_instances_policy=aws.autoscaling.GroupMixedInstancesPolicyArgs(
        launch_template=aws.autoscaling.GroupMixedInstancesPolicyLaunchTemplateArgs(
            launch_template_specification=aws.autoscaling.GroupMixedInstancesPolicyLaunchTemplateLaunchTemplateSpecificationArgs(
                launch_template_id=launch_template.id,
            ),
            overrides=auto_scaling_group_overrides,
        ),
        instances_distribution=aws.autoscaling.GroupMixedInstancesPolicyInstancesDistributionArgs(
            on_demand_allocation_strategy="prioritized",
            on_demand_base_capacity=0,
            on_demand_percentage_above_base_capacity=0,
            spot_allocation_strategy="price-capacity-optimized",
            spot_max_price="0.04",
        ),
    ),
    vpc_zone_identifiers=vpc.public_subnet_ids,
    tags=[
        aws.autoscaling.GroupTagArgs(
            key="Name",
            value=auto_scaling_group_name,
            propagate_at_launch=True,
        ),
        aws.autoscaling.GroupTagArgs(
            key="Project",
            value=project_name,
            propagate_at_launch=True,
        ),
        aws.autoscaling.GroupTagArgs(
            key="Env",
            value="dev",
            propagate_at_launch=True,
        ),
    ],
)

# Export the instance's publicly accessible IP address and hostname.
pulumi.export("aws_region", aws.get_region())
pulumi.export("ami", ami)
pulumi.export("azs", azs.names)
pulumi.export("vpc", vpc_name)
pulumi.export("security_group", security_group.id)
pulumi.export("launch_template", launch_template.id)
pulumi.export("auto_scaling_group", auto_scaling_group.id)

pulumi.export("ip", elastic_ip.public_ip)
pulumi.export("url", elastic_ip.public_ip.apply(lambda public_ip: f"http://{public_ip}"))
