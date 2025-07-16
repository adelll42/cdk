from aws_cdk import (
    Stack,
    aws_ecs as ecs,
    aws_ec2 as ec2,
    aws_ecr as ecr,
)
from constructs import Construct

class ECSServicesStack(Stack):
    def __init__(self, scope: Construct, id: str, vpc, cluster, **kwargs):
        super().__init__(scope, id, **kwargs)

        self.backend_service = self._create_service("backend", cluster)
        self.frontend_service = self._create_service("frontend", cluster)

    def _create_service(self, name: str, cluster: ecs.Cluster) -> ecs.Ec2Service:
        repo = ecr.Repository.from_repository_name(self, f"{name.capitalize()}Repo", name)
        task_def = ecs.Ec2TaskDefinition(self, f"{name.capitalize()}TaskDef")
        task_def.add_container(
            f"{name.capitalize()}Container",
            image=ecs.ContainerImage.from_ecr_repository(repo, tag="latest"),
            memory_reservation_mib=256,
            cpu=256,
            essential=True
        )

        return ecs.Ec2Service(
            self, f"{name.capitalize()}Service",
            cluster=cluster,
            task_definition=task_def,
            desired_count=1
        )
