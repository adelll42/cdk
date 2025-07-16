# separate_pipelines.py

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

        github_token_secret = secretsmanager.Secret.from_secret_name_v2(
            self, "BackendGithubTokenSecret", "github-token-adel"
        )

        repo = ecr.Repository.from_repository_name(self, "BackendECR", "backend")
        artifact_bucket = s3.Bucket(self, "BackendPipelineArtifacts")

        pipeline = codepipeline.Pipeline(self, "BackendPipeline", artifact_bucket=artifact_bucket)

        source_output = codepipeline.Artifact("BackendSourceOutput")
        build_output = codepipeline.Artifact("BackendBuildOutput")

        pipeline.add_stage(
            stage_name="Source",
            actions=[
                cpactions.GitHubSourceAction(
                    action_name="BackendSource",
                    owner="adelll42",
                    repo="trans-backend",
                    branch="main",
                    oauth_token=github_token_secret.secret_value_from_json("github-token-adel"),
                    output=source_output
                )
            ]
        )

        build_project = codebuild.PipelineProject(
            self, "BackendBuildProject",
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
                    action_name="BackendBuild",
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
                    action_name="DeployBackend",
                    service=service,
                    image_file=codepipeline.ArtifactPath(build_output, "backend-imagedefinitions.json")
                )
            ]
        )


class FrontendPipelineStack(Stack):
    def __init__(self, scope: Construct, id: str, *, vpc: ec2.Vpc, cluster: ecs.Cluster, service: ecs.BaseService, **kwargs):
        super().__init__(scope, id, **kwargs)

        github_token_secret = secretsmanager.Secret.from_secret_name_v2(
            self, "FrontendGithubTokenSecret", "github-token-adel"
        )

        repo = ecr.Repository.from_repository_name(self, "FrontendECR", "frontend")
        artifact_bucket = s3.Bucket(self, "FrontendPipelineArtifacts")

        pipeline = codepipeline.Pipeline(self, "FrontendPipeline", artifact_bucket=artifact_bucket)

        source_output = codepipeline.Artifact("FrontendSourceOutput")
        build_output = codepipeline.Artifact("FrontendBuildOutput")

        pipeline.add_stage(
            stage_name="Source",
            actions=[
                cpactions.GitHubSourceAction(
                    action_name="FrontendSource",
                    owner="adelll42",
                    repo="trans-frontend",
                    branch="main",
                    oauth_token=github_token_secret.secret_value_from_json("github-token-adel"),
                    output=source_output
                )
            ]
        )

        build_project = codebuild.PipelineProject(
            self, "FrontendBuildProject",
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
                    action_name="FrontendBuild",
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
                    action_name="DeployFrontend",
                    service=service,
                    image_file=codepipeline.ArtifactPath(build_output, "frontend-imagedefinitions.json")
                )
            ]
        )
