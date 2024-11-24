"""
Contains a Pulumi ComponentResource for creating a good-practice AWS VPC.
"""
from typing import Mapping, Sequence, Optional

import pulumi
import pulumi_aws as aws
import pulumi_awsx as awsx

class VpcxArgs:
    """
    The arguments necessary to construct a `Vpcx` resource.
    """

    def __init__(
            self,
            vpc_cidr_block: str | None = "10.0.0.0/16",
            # azs: pulumi.Input[Sequence[pulumi.Input[str]]] | pulumi.Input[str]  = aws.get_availability_zones(state="available").names,
            aws_region: pulumi.Input[str] = aws.get_region().name,
            sg_ingress_ports: Optional[pulumi.Input[Sequence[pulumi.Input[int]]]] = [22, 80, 443],
            tags: Optional[pulumi.Input[Mapping[str, pulumi.Input[str]]]] = {},
        ):
        """
        Constructs a VpcxArgs.

        :param vpc_cidr_block: The CIDR block representing the address space of the entire VPC.
        :param azs: A list of availability zone names in which to create subnets.
        :param aws_region: The name of a AWS Region for the VPC.
        :param sg_ingress_ports: Ingress ports for Security groups.
        :param tags: Tags which are applied to all taggable resources.
        """
        self.vpc_cidr_block = vpc_cidr_block
        # self.azs = [azs] if isinstance(azs, pulumi.Input) else azs
        self.azs = aws.get_availability_zones(state="available").names
        self.aws_region = aws_region
        self.sg_ingress_ports = sg_ingress_ports
        self.tags = tags

class Vpcx(pulumi.ComponentResource):
    """
    Creates a AWS VPC using Pulumi. The VPC consists of:

      - DHCP options for the given private hosted zone name
      - An Internet gateway
      - Subnets of appropriate sizes for public and private subnets, for each availability zone specified
      - A route table routing traffic from public subnets to the internet gateway
      - NAT gateways (and accoutrements) for each private subnet, and appropriate routing
      - Optionally, S3 and DynamoDB endpoints

    ### Example Usage

    ```python
    from vpc import Vpcx, VpcxArgs
    import pulumi
    import pulumi_aws as aws

    zones = aws.get_availability_zones(state="available")

    net = Vpcx("example-vpc", VpcxArgs(
        vpc_cidr_block="192.168.0.0/16",
        azs=zones.names,
        aws_region=aws.get_region().name,
        sg_ingress_ports=[22, 80, 443],
        tags={
            "Project": "Python Example VPC",
        },
    ))

    pulumi.export("vpc_id", net.vpc.id)
    pulumi.export("vpc_private_subnet_ids", net.vpc.private_subnet_ids)
    pulumi.export("vpc_public_subnet_ids", net.vpc.public_subnet_ids)
    pulumi.export("vpc_security_group_id", net.security_group.id)
    ```

    """

    def __init__(self,
                 name: str,
                 args: VpcxArgs,
                 opts: pulumi.ResourceOptions = None):
        """
        Constructs a Vpc.

        :param name: The Pulumi resource name. Child resource names are constructed based on this.
        :param args: A VpcArgs object containing the arguments for VPC constructin.
        :param opts: A pulumi.ResourceOptions object.
        """
        project_name = name if name else pulumi.get_project()
        super().__init__(f"{project_name}:VPCx", name, None, opts)

        # Make base info available to other methods
        self.name = name
        self.base_tags = args.tags

        # Create a vpc https://www.pulumi.com/docs/clouds/aws/guides/vpc/
        vpc_name = f"{project_name}-vpc"
        self.vpc = awsx.ec2.Vpc(
            vpc_name, 
            awsx.ec2.VpcArgs(
                cidr_block=args.vpc_cidr_block,
                number_of_availability_zones=len(args.azs),
                subnet_specs=[
                    awsx.ec2.SubnetSpecArgs(
                        type=awsx.ec2.SubnetType.PUBLIC,
                    ),
                    awsx.ec2.SubnetSpecArgs(
                        type=awsx.ec2.SubnetType.PRIVATE,
                    ),
                ],
                nat_gateways=awsx.ec2.NatGatewayConfigurationArgs(
                    strategy=awsx.ec2.NatGatewayStrategy.NONE,
                ),
                subnet_strategy=awsx.ec2.SubnetAllocationStrategy.AUTO,
                tags={ "Name": vpc_name, **args.tags },
            ),
            opts=pulumi.ResourceOptions( parent=self ),
        )

        ingress_sg = [
            aws.ec2.SecurityGroupIngressArgs(
                from_port=port,
                to_port=port,
                protocol="tcp",
                cidr_blocks=["0.0.0.0/0"],
            )
            for i, port in enumerate(args.sg_ingress_ports)
        ]

        egress_sg = [
            aws.ec2.SecurityGroupEgressArgs(
                from_port=0,
                to_port=0,
                protocol="-1",
                cidr_blocks=["0.0.0.0/0"],
            )
        ]

        # Create a security group allowing inbound access over "sg_ingress_ports" and outbound access to anywhere.
        security_group_name = f"{project_name}-security-group"
        self.security_group = aws.ec2.SecurityGroup(
            security_group_name,
            vpc_id=self.vpc.vpc_id,
            ingress=ingress_sg,
            egress=egress_sg,
            tags={ "Name": security_group_name, **args.tags },
            opts=pulumi.ResourceOptions( parent=self ),
        )

        super().register_outputs({
            "vpc_id": self.vpc.vpc_id,
            "security_group_id": self.security_group.id,
            "public_subnet_ids": self.vpc.public_subnet_ids,
            "private_subnet_ids": self.vpc.private_subnet_ids,
        })
