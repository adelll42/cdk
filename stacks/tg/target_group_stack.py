import os
import yaml
from aws_cdk import (
    Stack,
    aws_elasticloadbalancingv2 as elbv2,
    aws_ecs as ecs,
    aws_ec2 as ec2,
)
from constructs import Construct


class TargetGroupStack(Stack):
    def __init__(
            self, 
            scope: Construct, 
            id: str, 
            alb_listener: elbv2.ApplicationListener, 
            vpc: ec2.IVpc, 
            service_map: dict[str, ecs.FargateService], 
            **kwargs):
        super().__init__(scope, id, **kwargs)

        config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'load_balancer', 'target-groups.yml')
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        for tg_def in config.get("target_groups", []):
            name = tg_def["name"]
            port = tg_def["port"]
            targets_key = tg_def["targets"]
            service = service_map[targets_key]

            target_group = elbv2.ApplicationTargetGroup(
                self, f"{name}-TG",
                vpc=vpc,
                port=port,
                protocol=elbv2.ApplicationProtocol.HTTP,
                target_type=elbv2.TargetType.IP,
                health_check=elbv2.HealthCheck(
                    enabled=True,
                    path=tg_def.get("health_check", {}).get("path", "/"),
                    healthy_http_codes=tg_def.get("health_check", {}).get("healthy_http_codes", "200")
                )
            )

            target_group.add_target(service)

            for rule in tg_def.get("rules", []):
                alb_listener.add_targets(
                    f"{name}-Rule-{rule['priority']}",
                    priority=rule["priority"],
                    conditions=[elbv2.ListenerCondition.path_patterns([rule["path"]])],
                    target_group=target_group
                )
