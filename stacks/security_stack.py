from aws_cdk import (
    Stack,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
    aws_ecr_assets as ecr_assets,
    aws_rds as rds,
    aws_secretsmanager as secretsmanager,
    aws_ec2 as ec2,
    aws_ssm as ssm,
    aws_iam as iam,
    CfnOutput
)
from constructs import Construct
import os

class SecurityStack(Stack):

    def __init__(self, scope: Construct, id: str,vpc: ec2.Vpc, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        self.vpc = vpc

        prj_name = self.node.try_get_context("transendence")
        env_name = self.node.try_get_context("env")

        self.lambda_sg = ec2.SecurityGroup(self, 'lambdasg',
            security_group_name='tmp-lambda-sg',
            vpc=vpc,
            description="SG for Lambda Functions",
            allow_all_outbound=True
        )
        
        self.bastion_sg = ec2.SecurityGroup(self, 'bastionsg',
            security_group_name='tmp-bastion-sg',
            vpc=vpc,
            description="SG for Bastion Host",
            allow_all_outbound=True
        )

        self.bastion_sg.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(22), "SSH Access")
        
        redis_sg = ec2.SecurityGroup(self, 'redissg',
            security_group_name='tmp-redis-sg',
            vpc=vpc,
            description="SG for Redis Cluster",
            allow_all_outbound=True
        )
        redis_sg.add_ingress_rule(self.lambda_sg, ec2.Port.tcp(6379), 'Access from Lambda functions')

        self.ecs_sg = ec2.SecurityGroup(
            self, "TranscendenceSG",
            vpc=self.vpc,
            security_group_name='tmp-transcendence-sg',
            description="Allow HTTP and HTTPS",
            allow_all_outbound=True
        )

        self.db_sg = ec2.SecurityGroup(
            self, 'db-sg',
            security_group_name='tmp-db-sg',
            vpc=vpc,
            description="SG for RDS",
            allow_all_outbound=True
        )

        self.db_sg.add_ingress_rule(self.ecs_sg, ec2.Port.tcp(5432), "PostgreSQL access from ECS")

        CfnOutput(self, "DBSecurityGroupId", value=self.db_sg.security_group_id)

        self.ecs_task_role = iam.Role(
            self, "TranscendenceECSTaskRole",
            role_name="tmp-TranscendenceECSTaskRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            description="Role for ECS tasks to access S3 and Secrets Manager"
        )
        self.ecs_task_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3ReadOnlyAccess")
        )
        self.ecs_task_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("SecretsManagerReadWrite")
        )

        CfnOutput(self, "VpcId", value=self.vpc.vpc_id)
        CfnOutput(self, "SecurityGroupId", value=self.ecs_sg.security_group_id)