from aws_cdk import (
    Stack,
    aws_iam as iam,
)
from constructs import Construct

class IAMStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

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
