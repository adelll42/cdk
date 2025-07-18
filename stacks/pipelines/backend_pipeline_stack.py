import os
import yaml
from aws_cdk import (
    Stack,
    aws_codepipeline as codepipeline,
    aws_codepipeline_actions as cpactions,
    aws_codebuild as codebuild,
    aws_ecr as ecr,
    aws_iam as iam,
    aws_s3 as s3,
    aws_ec2 as ec2,
    aws_secretsmanager as secretsmanager,
    aws_ecs as ecs,
)
from constructs import Construct

class BackendPipelineStack(Stack):
    def __init__(self, scope: Construct, id: str, *, vpc: ec2.Vpc, cluster: ecs.Cluster, service: ecs.BaseService, **kwargs):
        super().__init__(scope, id, **kwargs)

        config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'pipelines', 'backend_pipeline.yml')
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        github = config["github"]
        pipeline_cfg = config["pipeline"]
        ecr_cfg = config["ecr"]
        build_cfg = config["codebuild"]
        deploy_cfg = config["deploy"]

        github_token_secret = secretsmanager.Secret.from_secret_name_v2(
            self, "GithubTokenSecret", github["token_secret_name"]
        )

        repo = ecr.Repository.from_repository_name(self, "BackendRepo", ecr_cfg["repository_name"])
        artifact_bucket = s3.Bucket(self, "PipelineBucket", bucket_name=pipeline_cfg["artifact_bucket_name"])

        pipeline = codepipeline.Pipeline(self, pipeline_cfg["name"], artifact_bucket=artifact_bucket)

        source_output = codepipeline.Artifact("SourceOutput")
        build_output = codepipeline.Artifact("BuildOutput")

        pipeline.add_stage(
            stage_name="Source",
            actions=[
                cpactions.GitHubSourceAction(
                    action_name="GitHubSource",
                    owner=github["owner"],
                    repo=github["repo"],
                    branch=github["branch"],
                    oauth_token=github_token_secret.secret_value_from_json(github["token_json_key"]),
                    output=source_output
                )
            ]
        )

        build_project = codebuild.PipelineProject(
            self, "BuildProject",
            environment=codebuild.BuildEnvironment(
                build_image=getattr(codebuild.LinuxBuildImage, build_cfg["image"]),
                privileged=build_cfg["privileged"]
            ),
            environment_variables={
                key: codebuild.BuildEnvironmentVariable(value=repo.repository_uri if val else val)
                for key, val in build_cfg["env_vars"].items()
            }
        )
        repo.grant_pull_push(build_project.role)

        pipeline.add_stage(
            stage_name="Build",
            actions=[
                cpactions.CodeBuildAction(
                    action_name="CodeBuild",
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
                    action_name="DeployService",
                    service=service,
                    image_file=codepipeline.ArtifactPath(build_output, deploy_cfg["image_def_path"])
                )
            ]
        )
