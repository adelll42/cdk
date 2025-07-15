#!/usr/bin/env python3
import aws_cdk as cdk

from stacks.vpc_stack import VpcStack
from stacks.security_stack import SecurityStack
from stacks.s3_stack import S3Stack
from stacks.codepipeline_backend import CodePipelineBackendStack
from stacks.ecs_stack import ECSStack

app = cdk.App()

vpc_stack = VpcStack(app, "vpc")

security_stack = SecurityStack(app, "security-stack", vpc=vpc_stack.vpc)

codepipeline_backend_stack = CodePipelineBackendStack(
    app,
    "codepipeline-backend",
    repo_name="your-repo-name",
    branch="main"
) 

s3_stack = S3Stack(app, "s3-stack")

ecs_stack = ECSStack(app, "ecs-stack", vpc=vpc_stack.vpc)

app.synth()
