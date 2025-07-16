from aws_cdk import Stack
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_elasticloadbalancingv2 as elbv2
from aws_cdk import aws_certificatemanager as acm
from aws_cdk import aws_ecs as ecs
from constructs import Construct


class ALBStack(Stack):
    def __init__(
        self,
        scope: Construct,
        id: str,
        *,
        vpc: ec2.Vpc,
        frontend_service: ecs.Ec2Service,
        backend_service: ecs.Ec2Service,
        certificate: acm.ICertificate,
        **kwargs
    ):
        super().__init__(scope, id, **kwargs)

        self.alb = elbv2.ApplicationLoadBalancer(
            self, "AppALB",
            vpc=vpc,
            internet_facing=True
        )

        # 🔁 HTTP → HTTPS redirect listener
        self.alb.add_listener(
            "HttpRedirect",
            port=80,
            open=True,
            default_action=elbv2.ListenerAction.redirect(
                protocol="HTTPS",
                port="443"
            )
        )

        # ✅ HTTPS listener
        https_listener = self.alb.add_listener(
            "HttpsListener",
            port=443,
            certificates=[certificate],
            open=True,
            default_target_groups=[
                elbv2.ApplicationTargetGroup(
                    self, "DefaultFrontendTG",
                    vpc=vpc,
                    port=80,
                    targets=[frontend_service]
                )
            ]
        )

        backend_target_group = elbv2.ApplicationTargetGroup(
            self, "BackendTargetGroup",
            vpc=vpc,
            port=3000,
            protocol=elbv2.ApplicationProtocol.HTTP,
            targets=[backend_service],
            health_check=elbv2.HealthCheck(
                path="/api/health",
                healthy_http_codes="200"
            )
        )


        frontend_target_group = elbv2.ApplicationTargetGroup(
            self, "FrontendTargetGroup",
            vpc=vpc,
            port=80,
            protocol=elbv2.ApplicationProtocol.HTTP,
            targets=[frontend_service]
        )

        # /api/* → backend
        https_listener.add_action(
            "BackendApiRule",
            priority=1,
            conditions=[elbv2.ListenerCondition.path_patterns(["/api/*"])],
            action=elbv2.ListenerAction.forward([backend_target_group])
        )

        # /avatars/* → backend
        https_listener.add_action(
            "BackendAvatarsRule",
            priority=2,
            conditions=[elbv2.ListenerCondition.path_patterns(["/avatars/*"])],
            action=elbv2.ListenerAction.forward([backend_target_group])
        )

        # Default → frontend
        https_listener.add_action(
            "FrontendDefaultRule",
            priority=10,
            conditions=[elbv2.ListenerCondition.path_patterns(["/*"])],
            action=elbv2.ListenerAction.forward([frontend_target_group])
        )


        self.listener = https_listener
