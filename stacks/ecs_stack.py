import aws_cdk as cdk
from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    CfnOutput
)
from constructs import Construct

class ECSClusterStack(Stack):
    def __init__(
        self, 
        scope: Construct, 
        id: str, 
        vpc: ec2.IVpc, 
        **kwargs
        ):

        super().__init__(scope, id, **kwargs)

        self.cluster = ecs.Cluster(self, "TranscendenceCluster",
                                   vpc=vpc,
                                   cluster_name="transcendence-cluster")

        self.cluster.add_capacity(
            "DefaultAutoScalingGroup",
            instance_type=ec2.InstanceType("t3.small"),
            min_capacity=1,
            max_capacity=2,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
        )

        CfnOutput(self, "ClusterName", value=self.cluster.cluster_name)
