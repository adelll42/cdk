#!/usr/bin/env python3
import aws_cdk as cdk
from aws_cdk import Environment
from aws_cdk import aws_secretsmanager as secretsmanager

from stacks.db_stack import DBStack
from stacks.vpc_stack import VpcStack
from stacks.security_stack import SecurityStack
from stacks.s3_stack import S3Stack
from stacks.ecs_services_stack import ECSServicesStack
from stacks.pipeline_stack import PipelineStack
from stacks.ecs_stack import ECSClusterStack


app = cdk.App()

env = Environment(account="577638398727", region="eu-west-2")

vpc_stack = VpcStack(
    app, 
    "vpc", 
    env=env
    )

security_stack = SecurityStack(
    app, 
    "security-stack", 
    vpc=vpc_stack.vpc, 
    env=env
    )

s3_stack = S3Stack(
    app, 
    "s3-stack", 
    env=env
    )

db_stack = DBStack(
    app,
    "db-stack",
    vpc=vpc_stack.vpc,
    db_sg=security_stack.db_sg,
    env=env
    )

ecs_stack = ECSClusterStack(
    app, 
    "ecs-cluster-stack", 
    vpc=vpc_stack.vpc, 
    env=env
    )

ecs_services_stack = ECSServicesStack(
    app,
    "ecs-services-stack",
    vpc=vpc_stack.vpc,
    cluster=ecs_stack.cluster,
    env=env
    )


pipeline_stack = PipelineStack(
    app,
    "pipeline",
    vpc=vpc_stack.vpc,
    cluster=ecs_stack.cluster,
    backend_service=ecs_services_stack.backend_service,
    frontend_service=ecs_services_stack.frontend_service,
    env=env
    )

app.synth()
