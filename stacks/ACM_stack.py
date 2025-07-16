from aws_cdk import Stack
from aws_cdk import aws_certificatemanager as acm
from aws_cdk import aws_route53 as route53
from constructs import Construct


class ACMStack(Stack):
    def __init__(
        self,
        scope: Construct, 
        id: str, *, 
        domain_name: str,
        **kwargs
        ):

        super().__init__(scope, id, **kwargs)

        hosted_zone = route53.HostedZone.from_lookup(
            self, "HostedZoneLookup",
            domain_name="dev.yospace.ai"
        )
        self.certificate = acm.Certificate(
            self, "SSLCertificate",
            domain_name=domain_name,
            validation=acm.CertificateValidation.from_dns(hosted_zone)
        )
