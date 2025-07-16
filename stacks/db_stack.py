from aws_cdk import (
    Stack,
    aws_rds as rds,
    aws_secretsmanager as secretsmanager,
    aws_ec2 as ec2,
    RemovalPolicy
)
from constructs import Construct

class DBStack(Stack):
    def __init__(
        self, 
        scope: Construct, 
        id: str, 
        vpc: ec2.Vpc, 
        db_sg: ec2.SecurityGroup, 
        **kwargs
        ):

        super().__init__(scope, id, **kwargs)
        
        db_secret = secretsmanager.Secret(
            self, "TranscendenceDBSecret",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template='{"username":"transcendence_admin"}',
                generate_string_key="password",
                exclude_punctuation=True
            )
        )
        db_instance = rds.DatabaseInstance(
            self, "TranscendencePostgres",
            engine=rds.DatabaseInstanceEngine.postgres(
                version=rds.PostgresEngineVersion.VER_14
            ),
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_ISOLATED),
            credentials=rds.Credentials.from_secret(db_secret),
            allocated_storage=20,
            max_allocated_storage=100,
            security_groups=[db_sg],
            publicly_accessible=False,
            removal_policy=RemovalPolicy.DESTROY
        )
