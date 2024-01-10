"""
Contains a Pulumi ComponentResource for creating a good-practice AWS VPC.
"""
import json
from typing import Mapping, Sequence

import pulumi
import pulumi_aws as aws
import pulumi_awsx as awsx

from .iam_helpers import assume_role_policy_for_principal
from .subnet_distributor import SubnetDistributor

class VpcArgs:
    """
    The arguments necessary to construct a `Vpc` resource.
    """

    def __init__(self,
                 description: str,
                 base_tags: Mapping[str, str],
                 base_cidr: str,
                 availability_zone_names: pulumi.Input[Sequence[pulumi.Input[str]]],
                 zone_name: pulumi.Input[str] = "",
                 create_s3_endpoint: bool = True,
                 create_dynamodb_endpoint: bool = True):
        """
        Constructs a VpcArgs.

        :param description: A human-readable description used to construct resource name tags.
        :param base_tags: Tags which are applied to all taggable resources.
        :param base_cidr: The CIDR block representing the address space of the entire VPC.
        :param availability_zone_names: A list of availability zone names in which to create subnets.
        :param zone_name: The name of a private Route 53 zone to create and set in a DHCP Option Set for the VPC.
        :param create_s3_endpoint: Whether or not to create a VPC endpoint and routes for S3 access.
        :param create_dynamodb_endpoint:  Whether or not to create a VPC endpoint and routes for DynamoDB access.
        """
        self.description = description
        self.base_tags = base_tags
        self.base_cidr = base_cidr
        self.availability_zone_names = availability_zone_names
        self.zone_name = zone_name
        self.create_s3_endpoint = create_s3_endpoint
        self.create_dynamodb_endpoint = create_dynamodb_endpoint

class Vpc(pulumi.ComponentResource):
    """
    Creates a good-practice AWS VPC using Pulumi. The VPC consists of:

      - DHCP options for the given private hosted zone name
      - An Internet gateway
      - Subnets of appropriate sizes for public and private subnets, for each availability zone specified
      - A route table routing traffic from public subnets to the internet gateway
      - NAT gateways (and accoutrements) for each private subnet, and appropriate routing
      - Optionally, S3 and DynamoDB endpoints

    ### Example Usage

    ```python
    from vpc import Vpc, VpcArgs
    from pulumi import export
    from pulumi_aws import get_availability_zones

    zones = get_availability_zones(state="available")

    vpc = Vpc("example-vpc", VpcArgs(
        description="Example VPC",
        base_tags={
            "Project": "Python Example VPC",
        },
        base_cidr="192.168.0.0/16",
        availability_zone_names=zones.names,
        zone_name="example.local",
        create_s3_endpoint=True,
        create_dynamodb_endpoint=True,
    ))
    vpc.enableFlowLoggingToCloudWatchLogs("ALL")

    export("vpcId", vpc.vpc.id)
    export("publicSubnetIds", [subnet.id for subnet in vpc.public_subnets])
    export("privateSubnetIds", [subnet.id for subnet in vpc.private_subnets])
    ```


    """

    def __init__(self,
                 name: str,
                 args: VpcArgs,
                 opts: pulumi.ResourceOptions = None):
        """
        Constructs a Vpc.

        :param name: The Pulumi resource name. Child resource names are constructed based on this.
        :param args: A VpcArgs object containing the arguments for VPC constructin.
        :param opts: A pulumi.ResourceOptions object.
        """
        project_name = name if name else pulumi.get_project()
        super().__init__(f"{project_name}:VPC", name, None, opts)

        # Make base info available to other methods
        self.name = name
        self.description = args.description
        self.base_tags = args.base_tags

        vpc_name = f"{project_name}-vpc"
        self.vpc = aws.ec2.Vpc(vpc_name,
                           cidr_block=args.base_cidr,
                           enable_dns_hostnames=True,
                           enable_dns_support=True,
                           tags={**args.base_tags, "Name": f"{args.description} VPC"},
                           opts=pulumi.ResourceOptions(
                               parent=self,
                           ))

        # Create VPC and Internet Gateway resources
        self.internet_gateway = aws.ec2.InternetGateway(f"{name}-igw",
                                                    vpc_id=self.vpc.id,
                                                    tags={**args.base_tags,
                                                          "Name": f"{args.description} VPC Internet Gateway"},
                                                    opts=pulumi.ResourceOptions(
                                                        parent=self.vpc,
                                                    ))

        # Calculate subnet CIDR blocks and create subnets
        subnet_distributor = SubnetDistributor(args.base_cidr, len(args.availability_zone_names))

        self.public_subnets = [aws.ec2.Subnet(f"{name}-public-subnet-{i}",
                                          vpc_id=self.vpc.id,
                                          cidr_block=cidr,
                                          availability_zone=args.availability_zone_names[i],
                                          map_public_ip_on_launch=True,
                                          tags={**args.base_tags, "Name": f"{args.description} Public Subnet {i}"},
                                          opts=pulumi.ResourceOptions(
                                              parent=self.vpc,
                                          ))
                               for i, cidr in enumerate(subnet_distributor.public_subnets)]

        self.private_subnets = [aws.ec2.Subnet(f"{name}-private-subnet-{i}",
                                           vpc_id=self.vpc.id,
                                           cidr_block=cidr,
                                           availability_zone=args.availability_zone_names[i],
                                           tags={**args.base_tags, "Name": f"{args.description} Private Subnet {i}"},
                                           opts=pulumi.ResourceOptions(
                                               parent=self.vpc,
                                           ))
                                for i, cidr in enumerate(subnet_distributor.private_subnets)]

        # Adopt the default route table for this VPC and adapt it for use with public subnets
        self.public_route_table = aws.ec2.DefaultRouteTable(f"{name}-public-rt",
                                                        default_route_table_id=self.vpc.default_route_table_id,
                                                        tags={**args.base_tags,
                                                              "Name": f"{args.description} Public Route Table"},
                                                        opts=pulumi.ResourceOptions(
                                                            parent=self.vpc,
                                                        ))

        aws.ec2.Route(f"{name}-route-public-sn-to-ig",
                  route_table_id=self.public_route_table.id,
                  destination_cidr_block="0.0.0.0/0",
                  gateway_id=self.internet_gateway.id,
                  opts=pulumi.ResourceOptions(
                      parent=self.public_route_table
                  ))

        for i, subnet in enumerate(self.public_subnets):
            aws.ec2.RouteTableAssociation(f"{name}-public-rta-{i + 1}",
                                      subnet_id=subnet.id,
                                      route_table_id=self.public_route_table,
                                      opts=pulumi.ResourceOptions(
                                          parent=self.public_route_table
                                      ))

        self.nat_elastic_ip_addresses: [aws.ec2.Eip] = list()
        self.nat_gateways: [aws.ec2.NatGateway] = list()
        self.private_route_tables: [aws.ec2.RouteTable] = list()

        # Create a NAT Gateway and appropriate route table for each private subnet
        for i, subnet in enumerate(self.private_subnets):
            self.nat_elastic_ip_addresses.append(aws.ec2.Eip(f"{name}-nat-{i + 1}",
                                                         tags={**args.base_tags,
                                                               "Name": f"{args.description} NAT Gateway EIP {i + 1}"},
                                                         opts=pulumi.ResourceOptions(
                                                             parent=subnet
                                                         )))

            self.nat_gateways.append(aws.ec2.NatGateway(f"{name}-nat-gateway-{i + 1}",
                                                    allocation_id=self.nat_elastic_ip_addresses[i].id,
                                                    subnet_id=self.public_subnets[i].id,
                                                    tags={**args.base_tags,
                                                          "Name": f"{args.description} NAT Gateway {i + 1}"},
                                                    opts=pulumi.ResourceOptions(
                                                        parent=subnet
                                                    )))

            self.private_route_tables.append(aws.ec2.RouteTable(f"{name}-private-rt-{i + 1}",
                                                            vpc_id=self.vpc.id,
                                                            tags={**args.base_tags,
                                                                  "Name": f"{args.description} Private RT {i + 1}"},
                                                            opts=pulumi.ResourceOptions(
                                                                parent=subnet
                                                            )))

            aws.ec2.Route(f"{name}-route-private-sn-to-nat-{i + 1}",
                      route_table_id=self.private_route_tables[i].id,
                      destination_cidr_block="0.0.0.0/0",
                      nat_gateway_id=self.nat_gateways[i].id,
                      opts=pulumi.ResourceOptions(
                          parent=self.private_route_tables[i]
                      ))

            aws.ec2.RouteTableAssociation(f"{name}-private-rta-{i + 1}",
                                      subnet_id=subnet.id,
                                      route_table_id=self.private_route_tables[i].id,
                                      opts=pulumi.ResourceOptions(
                                          parent=self.private_route_tables[i]
                                      ))

        # Create S3 endpoint if necessary
        if args.create_s3_endpoint:
            aws.ec2.VpcEndpoint(f"{name}-s3-endpoint",
                            vpc_id=self.vpc.id,
                            service_name=f"com.amazonaws.{aws.config.region}.s3",
                            route_table_ids=[self.public_route_table.id,
                                             *[rt.id for rt in self.private_route_tables]],
                            opts=pulumi.ResourceOptions(
                                parent=self.vpc
                            ))

        # Create DynamoDB endpoint if necessary
        if args.create_dynamodb_endpoint:
            aws.ec2.VpcEndpoint(f"{name}-dynamodb-endpoint",
                            vpc_id=self.vpc.id,
                            service_name=f"com.amazonaws.{aws.config.region}.dynamodb",
                            route_table_ids=[self.public_route_table.id,
                                             *[rt.id for rt in self.private_route_tables]],
                            opts=pulumi.ResourceOptions(
                                parent=self.vpc
                            ))

        super().register_outputs({})

    def enableFlowLoggingToS3(self, bucketArn: pulumi.Input[str], trafficType: pulumi.Input[str]):
        """
        Enable VPC flow logging to S3, for the specified traffic type
        :param self: VPC instance
        :param bucketArn: The arn of the s3 bucket to send logs to
        :param trafficType: The traffic type to log: "ALL", "ACCEPT" or "REJECT"
        :return: None
        """
        aws.ec2.FlowLog(f"{self.name}-flow-logs",
                    log_destination=bucketArn,
                    log_destination_type="s3",
                    vpc_id=self.vpc.id,
                    traffic_type=trafficType,
                    opts=pulumi.ResourceOptions(
                       parent=self.vpc,
                    ))

    def enableFlowLoggingToCloudWatchLogs(self, trafficType: pulumi.Input[str]):
        """
        Enable VPC flow logging to CloudWatch Logs, for the specified traffic type
        :param self: VPC instance
        :param trafficType: The traffic type to log: "ALL", "ACCEPT" or "REJECT"
        :return: None
        """
        self.flow_logs_role = aws.iam.Role(f"{self.name}-flow-logs-role",
                                       tags={**self.base_tags,
                                             "Name": f"{self.description} VPC Flow Logs"},
                                       assume_role_policy=assume_role_policy_for_principal({
                                           "Service": "vpc-flow-logs.amazonaws.com",
                                       }),
                                       opts=pulumi.ResourceOptions(
                                           parent=self.vpc,
                                       ))

        self.flow_logs_group = aws.cloudwatch.LogGroup(f"{self.name}-vpc-flow-logs",
                                                   tags={**self.base_tags,
                                                         "Name": f"{self.description} VPC Flow Logs"},
                                                   opts=pulumi.ResourceOptions(
                                                       parent=self.vpc,
                                                   ))

        aws.iam.RolePolicy(f"{self.name}-flow-log-policy",
                       name="vpc-flow-logs",
                       role=self.flow_logs_role.id,
                       policy=json.dumps({
                           "Version": "2012-10-17",
                           "Statement": [
                               {
                                   "Effect": "Allow",
                                   "Resource": "*",
                                   "Action": [
                                       "logs:CreateLogGroup",
                                       "logs:CreateLogStream",
                                       "logs:PutLogEvents",
                                       "logs:DescribeLogGroups",
                                       "logs:DescribeLogStreams",
                                   ]
                               }
                           ]
                       }),
                       opts=pulumi.ResourceOptions(
                           parent=self.flow_logs_role
                       ))

        aws.ec2.FlowLog(f"{self.name}-flow-logs",
                    log_destination=self.flow_logs_group.arn,
                    iam_role_arn=self.flow_logs_role.arn,
                    vpc_id=self.vpc.id,
                    traffic_type=trafficType,
                    opts=pulumi.ResourceOptions(
                        parent=self.flow_logs_role
                    ))

class VpcxArgs:
    """
    The arguments necessary to construct a `Vpcx` resource.
    """

    def __init__(self,
                 description: str,
                 base_tags: Mapping[str, str],
                 base_cidr: str,
                 availability_zone_names: pulumi.Input[Sequence[pulumi.Input[str]]],
                 zone_name: pulumi.Input[str] = "",
                 create_s3_endpoint: bool = True,
                 create_dynamodb_endpoint: bool = True):
        """
        Constructs a VpcxArgs.

        :param description: A human-readable description used to construct resource name tags.
        :param base_tags: Tags which are applied to all taggable resources.
        :param base_cidr: The CIDR block representing the address space of the entire VPC.
        :param availability_zone_names: A list of availability zone names in which to create subnets.
        :param zone_name: The name of a private Route 53 zone to create and set in a DHCP Option Set for the VPC.
        :param create_s3_endpoint: Whether or not to create a VPC endpoint and routes for S3 access.
        :param create_dynamodb_endpoint:  Whether or not to create a VPC endpoint and routes for DynamoDB access.
        """
        self.description = description
        self.base_tags = base_tags
        self.base_cidr = base_cidr
        self.availability_zone_names = availability_zone_names
        self.zone_name = zone_name
        self.create_s3_endpoint = create_s3_endpoint
        self.create_dynamodb_endpoint = create_dynamodb_endpoint


class Vpcx(pulumi.ComponentResource):
    """
    Creates a good-practice AWS VPC using Pulumi. The VPC consists of:

      - DHCP options for the given private hosted zone name
      - An Internet gateway
      - Subnets of appropriate sizes for public and private subnets, for each availability zone specified
      - A route table routing traffic from public subnets to the internet gateway
      - NAT gateways (and accoutrements) for each private subnet, and appropriate routing
      - Optionally, S3 and DynamoDB endpoints

    ### Example Usage

    ```python
    from vpc import Vpcx, VpcxArgs
    from pulumi import export
    from pulumi_aws import get_availability_zones

    zones = get_availability_zones(state="available")

    vpc = Vpcx("example-vpc", VpcxArgs(
        description="Example VPC",
        base_tags={
            "Project": "Python Example VPC",
        },
        base_cidr="192.168.0.0/16",
        availability_zone_names=zones.names,
        zone_name="example.local",
        create_s3_endpoint=True,
        create_dynamodb_endpoint=True,
    ))
    vpc.enableFlowLoggingToCloudWatchLogs("ALL")

    export("vpcId", vpc.vpc.id)
    export("publicSubnetIds", [subnet.id for subnet in vpc.public_subnets])
    export("privateSubnetIds", [subnet.id for subnet in vpc.private_subnets])
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
        self.description = args.description
        self.base_tags = args.base_tags

        # Create a vpc https://www.pulumi.com/docs/clouds/aws/guides/vpc/
        vpc_name = f"{project_name}-vpc"
        self.vpc = awsx.ec2.Vpc(
            vpc_name, 
            awsx.ec2.VpcArgs(
                cidr_block=args.vpc_network_cidr,
                number_of_availability_zones=len(args.azs.names),
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
                tags={ "Name": vpc_name, **args.base_tags },
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
            for i, port in enumerate(args.ingress_ports)
        ]

        self.sg = 


        self.vpc = aws.ec2.Vpc(vpc_name,
                           cidr_block=args.base_cidr,
                           enable_dns_hostnames=True,
                           enable_dns_support=True,
                           tags={**args.base_tags, "Name": f"{args.description} VPC"},
                           opts=pulumi.ResourceOptions(
                               parent=self,
                           ))

        # Create VPC and Internet Gateway resources
        self.internet_gateway = aws.ec2.InternetGateway(f"{name}-igw",
                                                    vpc_id=self.vpc.id,
                                                    tags={**args.base_tags,
                                                          "Name": f"{args.description} VPC Internet Gateway"},
                                                    opts=pulumi.ResourceOptions(
                                                        parent=self.vpc,
                                                    ))

        # Calculate subnet CIDR blocks and create subnets
        subnet_distributor = SubnetDistributor(args.base_cidr, len(args.availability_zone_names))

        self.public_subnets = [aws.ec2.Subnet(f"{name}-public-subnet-{i}",
                                          vpc_id=self.vpc.id,
                                          cidr_block=cidr,
                                          availability_zone=args.availability_zone_names[i],
                                          map_public_ip_on_launch=True,
                                          tags={**args.base_tags, "Name": f"{args.description} Public Subnet {i}"},
                                          opts=pulumi.ResourceOptions(
                                              parent=self.vpc,
                                          ))
                               for i, cidr in enumerate(subnet_distributor.public_subnets)]

        self.private_subnets = [aws.ec2.Subnet(f"{name}-private-subnet-{i}",
                                           vpc_id=self.vpc.id,
                                           cidr_block=cidr,
                                           availability_zone=args.availability_zone_names[i],
                                           tags={**args.base_tags, "Name": f"{args.description} Private Subnet {i}"},
                                           opts=pulumi.ResourceOptions(
                                               parent=self.vpc,
                                           ))
                                for i, cidr in enumerate(subnet_distributor.private_subnets)]

        # Adopt the default route table for this VPC and adapt it for use with public subnets
        self.public_route_table = aws.ec2.DefaultRouteTable(f"{name}-public-rt",
                                                        default_route_table_id=self.vpc.default_route_table_id,
                                                        tags={**args.base_tags,
                                                              "Name": f"{args.description} Public Route Table"},
                                                        opts=pulumi.ResourceOptions(
                                                            parent=self.vpc,
                                                        ))

        aws.ec2.Route(f"{name}-route-public-sn-to-ig",
                  route_table_id=self.public_route_table.id,
                  destination_cidr_block="0.0.0.0/0",
                  gateway_id=self.internet_gateway.id,
                  opts=pulumi.ResourceOptions(
                      parent=self.public_route_table
                  ))

        for i, subnet in enumerate(self.public_subnets):
            aws.ec2.RouteTableAssociation(f"{name}-public-rta-{i + 1}",
                                      subnet_id=subnet.id,
                                      route_table_id=self.public_route_table,
                                      opts=pulumi.ResourceOptions(
                                          parent=self.public_route_table
                                      ))

        self.nat_elastic_ip_addresses: [aws.ec2.Eip] = list()
        self.nat_gateways: [aws.ec2.NatGateway] = list()
        self.private_route_tables: [aws.ec2.RouteTable] = list()

        # Create a NAT Gateway and appropriate route table for each private subnet
        for i, subnet in enumerate(self.private_subnets):
            self.nat_elastic_ip_addresses.append(aws.ec2.Eip(f"{name}-nat-{i + 1}",
                                                         tags={**args.base_tags,
                                                               "Name": f"{args.description} NAT Gateway EIP {i + 1}"},
                                                         opts=pulumi.ResourceOptions(
                                                             parent=subnet
                                                         )))

            self.nat_gateways.append(aws.ec2.NatGateway(f"{name}-nat-gateway-{i + 1}",
                                                    allocation_id=self.nat_elastic_ip_addresses[i].id,
                                                    subnet_id=self.public_subnets[i].id,
                                                    tags={**args.base_tags,
                                                          "Name": f"{args.description} NAT Gateway {i + 1}"},
                                                    opts=pulumi.ResourceOptions(
                                                        parent=subnet
                                                    )))

            self.private_route_tables.append(aws.ec2.RouteTable(f"{name}-private-rt-{i + 1}",
                                                            vpc_id=self.vpc.id,
                                                            tags={**args.base_tags,
                                                                  "Name": f"{args.description} Private RT {i + 1}"},
                                                            opts=pulumi.ResourceOptions(
                                                                parent=subnet
                                                            )))

            aws.ec2.Route(f"{name}-route-private-sn-to-nat-{i + 1}",
                      route_table_id=self.private_route_tables[i].id,
                      destination_cidr_block="0.0.0.0/0",
                      nat_gateway_id=self.nat_gateways[i].id,
                      opts=pulumi.ResourceOptions(
                          parent=self.private_route_tables[i]
                      ))

            aws.ec2.RouteTableAssociation(f"{name}-private-rta-{i + 1}",
                                      subnet_id=subnet.id,
                                      route_table_id=self.private_route_tables[i].id,
                                      opts=pulumi.ResourceOptions(
                                          parent=self.private_route_tables[i]
                                      ))

        # Create S3 endpoint if necessary
        if args.create_s3_endpoint:
            aws.ec2.VpcEndpoint(f"{name}-s3-endpoint",
                            vpc_id=self.vpc.id,
                            service_name=f"com.amazonaws.{aws.config.region}.s3",
                            route_table_ids=[self.public_route_table.id,
                                             *[rt.id for rt in self.private_route_tables]],
                            opts=pulumi.ResourceOptions(
                                parent=self.vpc
                            ))

        # Create DynamoDB endpoint if necessary
        if args.create_dynamodb_endpoint:
            aws.ec2.VpcEndpoint(f"{name}-dynamodb-endpoint",
                            vpc_id=self.vpc.id,
                            service_name=f"com.amazonaws.{aws.config.region}.dynamodb",
                            route_table_ids=[self.public_route_table.id,
                                             *[rt.id for rt in self.private_route_tables]],
                            opts=pulumi.ResourceOptions(
                                parent=self.vpc
                            ))

        super().register_outputs({})
