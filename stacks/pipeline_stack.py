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

class PipelineStack(Stack):
    def __init__(
        self,
        scope: Construct,
        id: str,
        *,
        vpc: ec2.Vpc,
        cluster: ecs.Cluster,
        backend_service: ecs.BaseService,
        frontend_service: ecs.BaseService,
        **kwargs
    ):
        super().__init__(scope, id, **kwargs)

        github_token_secret = secretsmanager.Secret.from_secret_name_v2(
            self, "GithubTokenSecret", "github-token-adel"
        )

        pipeline = codepipeline.Pipeline(
            self, "TranscendencePipeline",
            artifact_bucket=s3.Bucket(self, "PipelineArtifacts")
        )

        backend_source_output = codepipeline.Artifact("BackendSourceOutput")
        frontend_source_output = codepipeline.Artifact("FrontendSourceOutput")

        pipeline.add_stage(
            stage_name="Source",
            actions=[
                cpactions.GitHubSourceAction(
                    action_name="BackendSourceAction",
                    owner="adelll42",
                    repo="trans-backend",
                    branch="main",
                    oauth_token=github_token_secret.secret_value_from_json("github-token-adel"),
                    output=backend_source_output
                ),
                cpactions.GitHubSourceAction(
                    action_name="FrontendSourceAction",
                    owner="adelll42",
                    repo="trans-frontend",
                    branch="main",
                    oauth_token=github_token_secret.secret_value_from_json("github-token-adel"),
                    output=frontend_source_output
                )
            ]
        )

        services = {
            "backend": {
                "service": backend_service,
                "source_output": backend_source_output
            },
            "frontend": {
                "service": frontend_service,
                "source_output": frontend_source_output
            }
        }

        for name, config in services.items():
            repo = ecr.Repository.from_repository_name(self, f"{name.capitalize()}ECR", name)
            build_output = codepipeline.Artifact(f"{name}BuildOutput")

            build_project = codebuild.PipelineProject(
                self, f"{name.capitalize()}BuildProject",
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
                stage_name=f"{name.capitalize()}Build",
                actions=[
                    cpactions.CodeBuildAction(
                        action_name=f"{name.capitalize()}BuildAction",
                        project=build_project,
                        input=config["source_output"],
                        outputs=[build_output]
                    )
                ]
            )

            pipeline.add_stage(
                stage_name=f"{name.capitalize()}Deploy",
                actions=[
                    cpactions.EcsDeployAction(
                        action_name=f"Deploy{name.capitalize()}",
                        service=config["service"],
                        input=build_output
                    )
                ]
            )
