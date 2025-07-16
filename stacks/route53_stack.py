from aws_cdk import Stack
from aws_cdk import aws_route53 as route53
from aws_cdk import aws_route53_targets as targets
from constructs import Construct
from aws_cdk.aws_elasticloadbalancingv2 import IApplicationLoadBalancer

class Route53Stack(Stack):
    def __init__(
        self, 
        scope: Construct,
        id: str,
        *,
        alb: IApplicationLoadBalancer,
        **kwargs
    ):
        super().__init__(scope, id, **kwargs)

        if not alb:
            raise ValueError("ALB must be provided to Route53Stack")

        hosted_zone = route53.HostedZone.from_lookup(
            self, "HostedZone",
            domain_name="dev.yospace.ai"
        )

        route53.ARecord(
            self, "AliasRecord",
            zone=hosted_zone,
            record_name="transendence",  # Full domain: transendence.dev.yospace.ai
            target=route53.RecordTarget.from_alias(targets.LoadBalancerTarget(alb))
        )
