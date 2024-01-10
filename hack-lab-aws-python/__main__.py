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
instance_types = config.get("instanceTypes") if config.get("instanceTypes") is not None else ['t3.micro', 't4g.small']
vpc_network_cidr = config.get("vpcNetworkCidr") if config.get("vpcNetworkCidr") is not None else "10.0.0.0/16"
keypair = config.get("keypair") if config.get("keypair") is not None else "jarvis"

