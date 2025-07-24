from aws_cdk import ( aws_ec2 as ec2, CfnOutput
)
from constructs import Construct
from helpers.tools import tools
class SecurityStack(tools):
    def __init__(
            self,
            scope: Construct,
            id: str,
            **kwargs
        ):
        
        super().__init__(scope, id, **kwargs)

        self.sg_lookup = {}

        config = self.load_yaml_config('config/security_group/security_groups.yml')

        for sg_def in config["security_groups"]:
            name = sg_def["name"]
            vpc_name = sg_def["vpc"]
            app_name = sg_def["app_name"]

            vpc_id = self.get_vpc_id(vpc_name)
            self.vpc = ec2.Vpc.from_vpc_attributes(
                self, self.logical_id_generator(app_name, vpc_name, name),
                vpc_id=vpc_id,
                availability_zones=self.availability_zones
            )

            sg = ec2.SecurityGroup(self, name,
                security_group_name=f"tmp-{name}", 
                vpc=self.vpc,
                description=sg_def.get("description", name),
                allow_all_outbound=sg_def.get("allow_all_outbound", True)
            )
            self.sg_lookup[name] = sg

            for rule in sg_def.get("ingress", []):
                protocol = rule["protocol"]
                from_port = rule["port"]
                to_port = rule.get("to_port", from_port) 
                description = rule.get("description", "")

                if "source_sg" in rule:
                    source_sg_name = rule["source_sg"]
                    if self.sg_lookup.get(source_sg_name):
                        source_peer = self.sg_lookup[source_sg_name]
                    else:
                        source_peer = ec2.Peer.ipv4(source_sg_name)

                else: 
                    source_peer = ec2.Peer.ipv4("0.0.0.0/0")

                
                sg.add_ingress_rule(
                    peer=source_peer,
                    connection=ec2.Port.tcp(from_port) if protocol == "tcp" else \
                                ec2.Port.udp(from_port) if protocol == "udp" else \
                                ec2.Port.all_traffic() if protocol == "all" else \
                                ec2.Port.icmp_type_code(from_port, to_port) if protocol == "icmp" else \
                                ec2.Port.from_protocol(protocol, from_port, to_port),
                    description=description
                )

            ssm_path = self.generate_ssm_parameter_path(app_name, name, "security-group")
            logical_id = self.logical_id_generator(app_name, name, "security-group")

            self.store_ssm_parameter(
                logical_id,
                parameter_name=ssm_path,
                string_value=self.sg_lookup[sg_def["name"]].security_group_id
            )


        if "ecs-sg" in self.sg_lookup:
            CfnOutput(self, "SecurityGroupId", value=self.sg_lookup["ecs-sg"].security_group_id)
        if "db-sg" in self.sg_lookup:
            CfnOutput(self, "DBSecurityGroupId", value=self.sg_lookup["db-sg"].security_group_id)