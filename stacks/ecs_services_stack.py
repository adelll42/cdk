import os
import yaml
from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecr as ecr,
    aws_secretsmanager as secretsmanager,
    aws_logs as logs,
    aws_iam as iam,
    aws_ssm as ssm
)
from constructs import Construct
from aws_cdk.aws_ecs import LogDrivers
from helpers.vpc_lookup import get_vpc_id


class ECSServicesStack(Stack):
    def __init__(
            self, 
            scope: Construct, 
            id: str,
            **kwargs
        ):

        super().__init__(scope, id, **kwargs)

        config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'ecs_services.yml')
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        vpc_id = get_vpc_id("transendence")
        vpc = ec2.Vpc.from_lookup(self, "VpcImported", vpc_id=vpc_id)

        cluster_name = ssm.StringParameter.value_for_string_parameter(
            self, "/transendence/transendence-cluster"
        )

        cluster = ecs.Cluster.from_cluster_attributes(
            self, "ClusterImported",
            cluster_name=cluster_name,
            vpc=vpc
        )

        task_role_arn = ssm.StringParameter.value_for_string_parameter(
            self, "/transendence/ecs-task-role-arn"
        )
        task_role = iam.Role.from_role_arn(self, "ImportedTaskRole", task_role_arn)

        for svc in config["services"]:
            self._create_service(
                name=svc["name"],
                repo_name=svc["repo"],
                port=svc["port"],
                secret_fields=svc.get("secrets", {}),
                cluster=cluster,
                task_role=task_role
            )

    def _create_service(self, name, repo_name, port, secret_fields, cluster, task_role):
        secret = secretsmanager.Secret.from_secret_name_v2(
            self, f"{name.capitalize()}Secrets", 
            "/JWT_EXPIRES_IN/JWT_SECRET/DEFAULT_AVATAR"
        ) ##### should be changed to match secrets

        repo = ecr.Repository.from_repository_name(
            self, f"{name.capitalize()}Repo", repo_name
        )

        log_group = logs.LogGroup(self, f"{name.capitalize()}LogGroup")

        task_def = ecs.Ec2TaskDefinition(self, f"{name.capitalize()}TaskDef", task_role=task_role)

        container = task_def.add_container(
            f"{name.capitalize()}Container",
            image=ecs.ContainerImage.from_ecr_repository(repo, tag="latest"),
            secrets={
                key: ecs.Secret.from_secrets_manager(secret, field=field)
                for key, field in secret_fields.items()
            },
            memory_reservation_mib=256,
            cpu=256,
            essential=True,
            logging=LogDrivers.aws_logs(
                stream_prefix=name,
                log_group=log_group
            )
        )

        container.add_port_mappings(
            ecs.PortMapping(container_port=port)
        )

        ecs.Ec2Service(
            self, f"{name.capitalize()}Service",
            cluster=cluster,
            task_definition=task_def,
            desired_count=1
        )
