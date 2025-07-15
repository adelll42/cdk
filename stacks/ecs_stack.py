import aws_cdk as cdk
from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_iam as iam,
    CfnOutput
)
from constructs import Construct

class ECSStack(Stack):
    def __init__(self, scope: Construct, id: str, vpc: ec2.IVpc, security_group: ec2.ISecurityGroup, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        cluster = ecs.Cluster(self, "TranscendenceCluster", vpc=vpc, cluster_name="transcendence-cluster")
        cluster.add_capacity(
            "DefaultAutoScalingGroup",
            instance_type=ec2.InstanceType("t3.micro"),
            min_capacity=1,
            max_capacity=2,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
        )

        task_definition = ecs.Ec2TaskDefinition(self, "TranscendenceTaskDef")
        log_driver = ecs.LogDriver.aws_logs(stream_prefix="Transcendence")
        container = task_definition.add_container(
            "AppContainer",
            image=ecs.ContainerImage.from_registry("amazon/amazon-ecs-sample"),
            memory_limit_mib=512,
            cpu=256,
            environment={"ENV": "dev"},
            logging=log_driver
        )
        container.add_port_mappings(ecs.PortMapping(container_port=80))

        task_definition.add_to_task_role_policy(
            iam.PolicyStatement(
                actions=["s3:GetObject", "s3:PutObject"],
                resources=["*"],  # Restrict to your bucket ARN in production!
            )
        )

        service = ecs.Ec2Service(
            self, "TranscendenceService",
            cluster=cluster,
            task_definition=task_definition,
            security_groups=[security_group],
            desired_count=1,
        )

        CfnOutput(self, "ClusterName", value=cluster.cluster_name)
        CfnOutput(self, "ServiceName", value=service.service_name)
        CfnOutput(self, "TaskDefinitionArn", value=task_definition.task_definition_arn)