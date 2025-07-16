from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    aws_s3 as s3
)
from constructs import Construct

class S3Stack(Stack):

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        self.bucket = s3.Bucket(self,
            "TranscendenceAppAssets",
            bucket_name="transcendence-app-assets",
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY,
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="AutoDeleteAfter30Days",
                    enabled=True,
                    expiration=Duration.days(30)
                )
            ],
            cors=[
                s3.CorsRule(
                    allowed_methods=[s3.HttpMethods.GET, s3.HttpMethods.PUT],
                    allowed_origins=["*"],
                    allowed_headers=["*"]
                )
            ]
        )

        self.frontend_prefix = "frontend/"
        self.uploads_prefix = "uploads/"
        self.artifacts_prefix = "artifacts/"
