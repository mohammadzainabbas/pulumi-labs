import pulumi
import pulumi_aws as aws
import pulumi_awsx as awsx
from vpc import Vpcx, VpcxArgs
import base64
from json import loads
from utils import DownloadUnzip

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
azs = aws.get_availability_zones(state="available").names[0]

# Create a VPC with a size /16 CIDR block
vpc = Vpcx(
    project_name,
    VpcxArgs(
        vpc_cidr_block=vpc_network_cidr,
        azs=azs,
        sg_ingress_ports=[22, 80],
        tags={
            "Project": project_name,
            "Environment": "dev",
        },
    ),
)

# Create a hacker machine
hacker_instance_name = f"{project_name}-kali"
hacker_instance = aws.ec2.Instance(
    hacker_instance_name,
    ami=ami,
    instance_type="r5dn.4xlarge",
    instance_market_options=aws.ec2.InstanceInstanceMarketOptionsArgs(
        market_type="spot",
        spot_options=aws.ec2.InstanceInstanceMarketOptionsSpotOptionsArgs(
            max_price="0.5",
            spot_instance_type="one-time",
        ),
    ),
    key_name=keypair,
    vpc_security_group_ids=[vpc.security_group.id],
    subnet_id=vpc.vpc.public_subnet_ids[0],
    user_data=(lambda path: base64.b64encode(open(path).read().encode()).decode())(f"{user_data_file}"),
    tags={
        "Name": "kali",
        "Project": project_name,
        "Environment": "dev",
    },
)

# Create a s3 bucket
bucket_name = f"{project_name}-bucket"
bucket = aws.s3.BucketV2(
    bucket_name,
    tags={
        "Name": bucket_name,
        "Project": project_name,
        "Environment": "dev",
    },
)

public_access_block = aws.s3.BucketPublicAccessBlock(
    f"{bucket_name}-public-access-block",
    block_public_acls=False,
    block_public_policy=False,
    ignore_public_acls=False,
    restrict_public_buckets=True,
    bucket=bucket.id,
)

vuln_os_file = f"breach.zip"
vuln_os_output_dir = f"~/Desktop/vuln"
vuln_os_url = f"https://download.vulnhub.com/breach/Breach-1.0.zip"
vuln_os_name = f"{project_name}-breach-vm"
vuln_os = DownloadUnzip(
    vuln_os_name,
    url=vuln_os_url,
    output_dir=vuln_os_output_dir,
    filename=vuln_os_file,
)

# Export the instance's publicly accessible IP address and hostname.
pulumi.export("aws_region", aws_region)
pulumi.export("ami", ami)
pulumi.export("azs", azs)
pulumi.export("vpc_id", vpc.vpc.vpc_id)
pulumi.export("security_group_id", vpc.security_group.id)
pulumi.export("public_subnet_ids", vpc.vpc.public_subnet_ids)
pulumi.export("private_subnet_ids", vpc.vpc.private_subnet_ids)
pulumi.export("hacker_instance", hacker_instance.public_ip)
pulumi.export("bucket", bucket.bucket_domain_name)
