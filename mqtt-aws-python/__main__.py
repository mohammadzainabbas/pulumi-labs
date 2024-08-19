import pulumi
import pulumi_aws as aws
import pulumi_awsx as awsx

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

# Create a new VPC
vpc = aws.ec2.Vpc("mqtt-vpc",
    cidr_block="10.0.0.0/16",
    enable_dns_support=True,
    enable_dns_hostnames=True,
    tags={
        "Name": "mqtt-vpc",
    }
)

# Create a public subnet
subnet = aws.ec2.Subnet("publicSubnet",
    vpc_id=vpc.id,
    cidr_block="10.0.1.0/24",
    map_public_ip_on_launch=True,
    tags={
        "Name": "publicSubnet",
    }
)

# Create an internet gateway
internet_gateway = aws.ec2.InternetGateway("internetGateway",
    vpc_id=vpc.id,
    tags={
        "Name": "internetGateway",
    }
)

# Create a route table
route_table = aws.ec2.RouteTable("routeTable",
    vpc_id=vpc.id,
    routes=[
        aws.ec2.RouteTableRouteArgs(
            cidr_block="0.0.0.0/0",
            gateway_id=internet_gateway.id,
        ),
    ],
    tags={
        "Name": "routeTable",
    }
)

# Associate route table with subnet
route_table_association = aws.ec2.RouteTableAssociation("routeTableAssociation",
    subnet_id=subnet.id,
    route_table_id=route_table.id
)

# Define an Amazon MQ Broker
broker = aws.mq.Broker("simpleActiveMQBroker",
    broker_name="simple-activemq-broker",
    engine_type="ActiveMQ",
    engine_version="5.16.7",
    host_instance_type="mq.t3.micro",
    security_groups=[],  # Add security group IDs if needed
    subnet_ids=[subnet.id],  # Subnet where the broker should be deployed
    publicly_accessible=False,
    users=[aws.mq.BrokerUserArgs(
        username="admin",
        password="ChangeMe123!",  # Change to a secure password
    )],
    logs=aws.mq.BrokerLogsArgs(
        general=True,
    ),
    tags={
        "environment": "dev"
    }
)

pulumi.export("broker_id", broker.id)
pulumi.export("broker_arn", broker.arn)
pulumi.export("broker_url", broker.instances[0].endpoints[0])