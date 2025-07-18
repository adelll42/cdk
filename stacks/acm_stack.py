from aws_cdk import (
    Stack,
    aws_certificatemanager as acm,
    aws_route53 as route53,
    aws_ssm as ssm
)
from constructs import Construct
import os
import yaml


class ACMStack(Stack):
    def __init__(
            self, 
            scope: Construct, 
            id: str, 
            **kwargs
        ):
        super().__init__(scope, id, **kwargs)

        config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'acm.yml')
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        certs = config.get("certificates", [])

        for cert_def in certs:
            cert_id = cert_def["id"]
            domain_name = cert_def["domain_name"]
            hosted_zone_name = cert_def["hosted_zone"]

            hosted_zone = route53.HostedZone.from_lookup(
                self, f"{cert_id}-Zone",
                domain_name=hosted_zone_name
            )

            certificate = acm.Certificate(
                self, f"{cert_id}-Certificate",
                domain_name=domain_name,
                validation=acm.CertificateValidation.from_dns(hosted_zone)
            )

            ssm.StringParameter(
                self, f"{cert_id}-CertArn",
                parameter_name=f"/transendence/certificates/{cert_id}/arn",
                string_value=certificate.certificate_arn
            )
