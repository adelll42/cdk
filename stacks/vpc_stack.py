from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_ssm as ssm,
)
from constructs import Construct
import yaml
import os
import random
from helpers.get_or_create_parameter import get_or_create_parameter


class VpcStack(Stack):

    def __init__(
            self,
            scope: Construct,
            construct_id: str,
            **kwargs
            ):
        
        super().__init__(scope, construct_id, **kwargs)

        config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'vpcs.yml')
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)

        vpcs = config.get("vpcs", [])

        for vpc_def in vpcs:
            name = vpc_def["name"]
            cidr = vpc_def["cidr"]
            nat_gateways = vpc_def.get("nat_gateways", 0)
            subnet_defs = vpc_def.get("subnets", [])
            max_azs = vpc_def.get("max_azs", 2)
            enable_dns_support = vpc_def.get("enable_dns_support", True)
            enable_dns_hostnames = vpc_def.get("enable_dns_hostnames", True)


            subnet_configs = []
            for subnet in subnet_defs:
                subnet_configs.append(
                    ec2.SubnetConfiguration(
                        name=subnet["name"],
                        subnet_type=ec2.SubnetType[subnet["type"]],
                        cidr_mask=subnet["cidr_mask"]
                    )
                )

            logical_id_param = f"/transcendence/vpc-logical-id/{name}"
            random_id = f"vpc-{name}-{random.randint(1000, 9999)}"
            logical_id = get_or_create_parameter(logical_id_param, random_id)

            vpc = ec2.Vpc(self, logical_id,
                vpc_name=logical_id,
                cidr=cidr,
                max_azs=max_azs,
                subnet_configuration=subnet_configs,
                nat_gateways=nat_gateways,
                enable_dns_support=enable_dns_support,
                enable_dns_hostnames=enable_dns_hostnames
            )


            ssm.StringParameter(self, f"VpcId-{name}",
                parameter_name=f"/transcendence/vpc-id/{name}",
                string_value=vpc.vpc_id
            )

            for i, subnet in enumerate(vpc.private_subnets, 1):
                ssm.StringParameter(self, f"{name}-private-subnet-{i}",
                    parameter_name=f"/transcendence/{name}/private-subnet-{i}",
                    string_value=subnet.subnet_id
                )

            
            for i, subnet in enumerate(vpc.public_subnets, 1):
                ssm.StringParameter(self, f"{name}-public-subnet-{i}",
                    parameter_name=f"/transcendence/{name}/public-subnet-{i}",
                    string_value=subnet.subnet_id
                )

