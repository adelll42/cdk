import os
import yaml
from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_elasticloadbalancingv2 as elbv2,
    aws_certificatemanager as acm,
    aws_ssm as ssm,

    aws_ecs as ecs
)
from constructs import Construct

from helpers.vpc_lookup import get_vpc_id

class ALBStack(Stack):
    def __init__(
        self,
        scope: Construct,
        id: str,
        **kwargs
    ):
        super().__init__(scope, id, **kwargs)

        # Load YAML config
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'alb', 'alb.yml')
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        vpc_name = config["vpc"]["name"]
        vpc_id = get_vpc_id(vpc_name)
        vpc = ec2.Vpc.from_lookup(self, "VpcImported", vpc_id=vpc_id)
        cert_id = "dev-cert"  # Or read from config if you like

        cert_param = ssm.StringParameter.from_string_parameter_attributes(
            self, "ImportedCertParam",
            parameter_name=f"/transendence/certificates/{cert_id}/arn",
            simple_name=False  # because it starts with a slash
        )

        cert_arn = cert_param.string_value

        certificate = acm.Certificate.from_certificate_arn(
            self, "ImportedCertificate", cert_arn
        )


        cluster_name = config["cluster"]["name"]

        cluster = ecs.Cluster.from_cluster_attributes(
            self, "ClusterImported",
            cluster_name=cluster_name,
            vpc=vpc
        )

        services = {}
        for svc in config["alb"]["services"]:
            service_name = ssm.StringParameter.value_for_string_parameter(
                self, svc["ecs_service_ssm_param"]
            )
            services[svc["name"]] = ecs.Ec2Service.from_ec2_service_attributes(
                self, f"{svc['name'].capitalize()}ServiceImported",
                cluster=cluster,
                service_name=service_name
            )
        frontend_service = services.get("frontend")
        backend_service = services.get("backend")
        self.alb = elbv2.ApplicationLoadBalancer(
            self, config['alb']['name'],
            vpc=vpc,
            internet_facing=True
        )

        # Create target groups based on YAML config
        tg_defs = config['alb']['target_groups']
        self.target_groups = {
            'frontend': self._create_target_group("FrontendTG", vpc, tg_defs['frontend']),
            'backend': self._create_target_group("BackendTG", vpc, tg_defs['backend'])
        }

        if config.get('redirect_http', True):
            self._add_http_redirect_listener()

        self.https_listener = self._add_https_listener(certificate, config['alb']['routing'])

    def _create_target_group(self, id, vpc, cfg):
        return elbv2.ApplicationTargetGroup(
            self, id,
            vpc=vpc,
            port=cfg['port'],
            protocol=elbv2.ApplicationProtocol.HTTP,
            target_type=elbv2.TargetType.IP,  # ✅ use IP-based targets
            health_check=elbv2.HealthCheck(
                path=cfg.get('health_path', '/'),
                healthy_http_codes="200"
            )
        )


    def _add_http_redirect_listener(self):
        self.alb.add_listener(
            "HttpRedirectListener",
            port=80,
            open=True,
            default_action=elbv2.ListenerAction.redirect(
                protocol="HTTPS",
                port="443"
            )
        )

    def _add_https_listener(self, certificate, routes):
        listener = self.alb.add_listener(
        "HttpsListener",
        port=443,
        open=True,
        certificates=[certificate],
        default_action=elbv2.ListenerAction.forward([self.target_groups["frontend"]])  # 👈 fallback default
    )

        for route in routes:
            target_group = self.target_groups[route['target']]
            listener.add_action(
                route['name'],
                priority=route['priority'],
                conditions=[elbv2.ListenerCondition.path_patterns([route['path']])],
                action=elbv2.ListenerAction.forward([target_group])
            )

        return listener
    
        ssm.StringParameter(
            self, "ALBEndpoint",
            parameter_name="/transendence/alb/endpoint",
            string_value=self.alb.load_balancer_dns_name
        )