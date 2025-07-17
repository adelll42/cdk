#!/usr/bin/env python3
import aws_cdk as cdk
from aws_cdk import Environment
from aws_cdk import aws_secretsmanager as secretsmanager
from aws_cdk import aws_route53 as route53

from stacks.db_stack import DBStack
from stacks.vpc_stack import VpcStack
from stacks.security_stack import SecurityStack
from stacks.s3_stack import S3Stack
from stacks.ecs_services_stack import ECSServicesStack
from stacks.pipeline_stack import BackendPipelineStack, FrontendPipelineStack
from stacks.ecs_stack import ECSClusterStack
from stacks.alb_stack import ALBStack
from stacks.ACM_stack import ACMStack
from stacks.route53_stack import Route53Stack
from stacks.waf_stack import WAFStack


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


backend_pipeline_stack = BackendPipelineStack(
    app,
    "backend-pipeline-stack",
    vpc=vpc_stack.vpc,
    cluster=ecs_stack.cluster,
    service=ecs_services_stack.backend_service,
    env=env
)

frontend_pipeline_stack = FrontendPipelineStack(
    app,
    "frontend-pipeline",
    vpc=vpc_stack.vpc,
    cluster=ecs_stack.cluster,
    service=ecs_services_stack.frontend_service,
    env=env
)

acm_stack = ACMStack(
    app,
    "acm-stack",
    domain_name="transendence.dev.yospace.ai",
    env=env
)

alb_stack = ALBStack(
    app,
    "alb-stack",
    vpc=vpc_stack.vpc,
    frontend_service=ecs_services_stack.frontend_service,
    backend_service=ecs_services_stack.backend_service,
    certificate=acm_stack.certificate,
    env=env
)

route53_stack = Route53Stack(
    app,
    "route53-stack",
    alb=alb_stack.alb,
    env=env
)

waf_stack = WAFStack(
    app,
    "waf-stack",
    alb=alb_stack.alb,
    env=env
)


app.synth()
