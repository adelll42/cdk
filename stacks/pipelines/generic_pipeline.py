from aws_cdk import (
    Stack,
    aws_codepipeline as codepipeline,
    aws_codepipeline_actions as cpactions,
    aws_codebuild as codebuild,
    aws_ecr as ecr,
    aws_s3 as s3,
    aws_ec2 as ec2,
    aws_secretsmanager as secretsmanager,
    aws_ecs as ecs,
    aws_ssm as ssm
)
from constructs import Construct
from helpers.tools import tools


class GenericPipelineStack(tools):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        config = self.load_yaml_config('config/pipelines/pipelines.yml')

        aws_service = "pipelineStack"

        for pipeline_def in config.get("pipelines", []):
            name = pipeline_def["name"]
            vpc_id = self.get_vpc_id(pipeline_def["vpc"])
            vpc = ec2.Vpc.from_lookup(self, f"{name}-VpcImported-{aws_service}", vpc_id=vpc_id)

            cluster = ecs.Cluster.from_cluster_attributes(
                self, f"{name}-ClusterImported-{aws_service}",
                cluster_name=pipeline_def["cluster"],
                vpc=vpc
            )

            service = ecs.Ec2Service.from_ec2_service_attributes(
                self, f"{name}-ServiceImported-{aws_service}",
                cluster=cluster,
                service_name=name
            )

            self._create_pipeline(
                name=name,
                github=pipeline_def["github"],
                ecr_repo_name=pipeline_def["ecr_repo"],
                image_def_file=pipeline_def["image_definition_file"],
                service=service
            )

    def _create_pipeline(self, name, github, ecr_repo_name, image_def_file, service):
        secret = secretsmanager.Secret.from_secret_name_v2(
            self, f"{name}GitHubToken", github["secret_name"]
        )

        repo = ecr.Repository.from_repository_name(self, f"{name}Repo", ecr_repo_name)
        bucket = s3.Bucket(self, f"{name}PipelineArtifacts")

        pipeline = codepipeline.Pipeline(self, f"{name}Pipeline", artifact_bucket=bucket)

        source_output = codepipeline.Artifact(f"{name}SourceOutput")
        build_output = codepipeline.Artifact(f"{name}BuildOutput")

        pipeline.add_stage(
            stage_name="Source",
            actions=[
                cpactions.GitHubSourceAction(
                    action_name="GitHub_Source",
                    owner=github["owner"],
                    repo=github["repo"],
                    branch=github["branch"],
                    oauth_token=secret.secret_value,
                    output=source_output
                )
            ]
        )

        build_project = codebuild.PipelineProject(
            self, f"{name}BuildProject",
            environment=codebuild.BuildEnvironment(
                build_image=codebuild.LinuxBuildImage.STANDARD_7_0,
                privileged=True
            ),
            environment_variables={
                "REPOSITORY_URI": codebuild.BuildEnvironmentVariable(value=repo.repository_uri)
            }
        )
        repo.grant_pull_push(build_project.role)

        pipeline.add_stage(
            stage_name="Build",
            actions=[
                cpactions.CodeBuildAction(
                    action_name="Docker_Build",
                    project=build_project,
                    input=source_output,
                    outputs=[build_output]
                )
            ]
        )

        pipeline.add_stage(
            stage_name="Deploy",
            actions=[
                cpactions.EcsDeployAction(
                    action_name="ECS_Deploy",
                    service=service,
                    image_file=codepipeline.ArtifactPath(build_output, image_def_file)
                )
            ]
        )

