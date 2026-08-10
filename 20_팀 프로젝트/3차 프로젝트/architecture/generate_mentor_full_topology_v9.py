from __future__ import annotations

import argparse
import base64
import html
import math
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


HERE = Path(__file__).resolve().parent
PAGE_W = 3600
PAGE_H = 2200
FONT_REGULAR = Path(r"C:\Windows\Fonts\malgun.ttf")
FONT_BOLD = Path(r"C:\Windows\Fonts\malgunbd.ttf")
ICON_CACHE = Path.home() / "AppData/Local/Temp/codex-aws-icons-04302026"
SERVICE_ICONS = ICON_CACHE / "Architecture-Service-Icons_04302026"
RESOURCE_ICONS = ICON_CACHE / "Resource-Icons_04302026"
GROUP_ICONS = ICON_CACHE / "Architecture-Group-Icons_04302026"


C = {
    "bg": "#F4F6F8",
    "white": "#FFFFFF",
    "ink": "#232F3E",
    "muted": "#5F6B7A",
    "line": "#879596",
    "border": "#D5DBDB",
    "foundation": "#147EBA",
    "foundation_fill": "#F4FAFD",
    "daily": "#C45500",
    "daily_fill": "#FFF8EE",
    "dr": "#8C4FFF",
    "dr_fill": "#FAF7FF",
    "opt": "#7AA116",
    "opt_fill": "#F5FAEE",
    "network": "#00A4A6",
    "public_fill": "#F1F8EC",
    "private_fill": "#EAF9F7",
    "data_fill": "#F4F0FF",
    "obs": "#E7157B",
    "obs_fill": "#FFF7FB",
    "request": "#147EBA",
    "deploy": "#1D8102",
    "operations": "#00A4A6",
    "replication": "#C45500",
    "telemetry": "#E7157B",
}


ICON_PATHS = {
    "route53": SERVICE_ICONS / "Arch_Networking-Content-Delivery/64/Arch_Amazon-Route-53_64.png",
    "cloudfront": SERVICE_ICONS / "Arch_Networking-Content-Delivery/64/Arch_Amazon-CloudFront_64.png",
    "waf": SERVICE_ICONS / "Arch_Security-Identity/64/Arch_AWS-WAF_64.png",
    "acm": SERVICE_ICONS / "Arch_Security-Identity/64/Arch_AWS-Certificate-Manager_64.png",
    "iam": SERVICE_ICONS / "Arch_Security-Identity/64/Arch_AWS-Identity-and-Access-Management_64.png",
    "ssm": SERVICE_ICONS / "Arch_Management-Tools/64/Arch_AWS-Systems-Manager_64.png",
    "ecr": SERVICE_ICONS / "Arch_Containers/64/Arch_Amazon-Elastic-Container-Registry_64.png",
    "s3": SERVICE_ICONS / "Arch_Storage/64/Arch_Amazon-Simple-Storage-Service_64.png",
    "alb": SERVICE_ICONS / "Arch_Networking-Content-Delivery/64/Arch_Elastic-Load-Balancing_64.png",
    "eks": SERVICE_ICONS / "Arch_Containers/64/Arch_Amazon-Elastic-Kubernetes-Service_64.png",
    "ec2": SERVICE_ICONS / "Arch_Compute/64/Arch_Amazon-EC2_64.png",
    "rds": SERVICE_ICONS / "Arch_Databases/64/Arch_Amazon-RDS_64.png",
    "valkey": SERVICE_ICONS / "Arch_Databases/64/Arch_Amazon-ElastiCache_64.png",
    "efs": SERVICE_ICONS / "Arch_Storage/64/Arch_Amazon-EFS_64.png",
    "cloudwatch": SERVICE_ICONS / "Arch_Management-Tools/64/Arch_Amazon-CloudWatch_64.png",
    "cloudtrail": SERVICE_ICONS / "Arch_Management-Tools/64/Arch_AWS-CloudTrail_64.png",
    "guardduty": SERVICE_ICONS / "Arch_Security-Identity/64/Arch_Amazon-GuardDuty_64.png",
    "eventbridge": SERVICE_ICONS / "Arch_Application-Integration/64/Arch_Amazon-EventBridge_64.png",
    "sns": SERVICE_ICONS / "Arch_Application-Integration/64/Arch_Amazon-Simple-Notification-Service_64.png",
    "athena": SERVICE_ICONS / "Arch_Analytics/64/Arch_Amazon-Athena_64.png",
    "vpc": SERVICE_ICONS / "Arch_Networking-Content-Delivery/64/Arch_Amazon-Virtual-Private-Cloud_64.png",
    "nat": RESOURCE_ICONS / "Res_Networking-Content-Delivery/Res_Amazon-VPC_NAT-Gateway_48.png",
    "igw": RESOURCE_ICONS / "Res_Networking-Content-Delivery/Res_Amazon-VPC_Internet-Gateway_48.png",
    "user": RESOURCE_ICONS / "Res_General-Icons/Res_48_Dark/Res_Users_48_Dark.png",
    "source": RESOURCE_ICONS / "Res_General-Icons/Res_48_Dark/Res_Source-Code_48_Dark.png",
    "toolkit": RESOURCE_ICONS / "Res_General-Icons/Res_48_Dark/Res_Toolkit_48_Dark.png",
    "server": RESOURCE_ICONS / "Res_General-Icons/Res_48_Dark/Res_Server_48_Dark.png",
    "cloud_group": GROUP_ICONS / "AWS-Cloud_32.png",
    "region_group": GROUP_ICONS / "Region_32.png",
    "vpc_group": GROUP_ICONS / "Virtual-private-cloud-VPC_32.png",
    "public_group": GROUP_ICONS / "Public-subnet_32.png",
    "private_group": GROUP_ICONS / "Private-subnet_32.png",
}


@dataclass
class Box:
    box_id: str
    label: str
    x: int
    y: int
    w: int
    h: int
    kind: str
    parent: str = "layer-topology"
    icon: str | None = None
    stroke: str = C["border"]
    fill: str = C["white"]
    dashed: bool = False
    badge: str | None = None
    font_size: int = 24
    z: int = 10
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass
class Edge:
    edge_id: str
    source: str
    target: str
    layer: str
    color: str
    label: str = ""
    dashed: bool = False
    width: int = 4
    exit_xy: tuple[float, float] = (1.0, 0.5)
    entry_xy: tuple[float, float] = (0.0, 0.5)
    points: list[tuple[int, int]] = field(default_factory=list)


BOXES: list[Box] = []
EDGES: list[Edge] = []


def add(box: Box) -> Box:
    BOXES.append(box)
    return box


def edge(
    edge_id: str,
    source: str,
    target: str,
    layer: str,
    color: str,
    *,
    label: str = "",
    dashed: bool = False,
    width: int = 4,
    exit_xy: tuple[float, float] = (1.0, 0.5),
    entry_xy: tuple[float, float] = (0.0, 0.5),
    points: list[tuple[int, int]] | None = None,
) -> None:
    EDGES.append(
        Edge(
            edge_id,
            source,
            target,
            layer,
            color,
            label,
            dashed,
            width,
            exit_xy,
            entry_xy,
            points or [],
        )
    )


def build_boxes() -> None:
    # Header and legend.
    add(Box("header-accent", "", 0, 0, PAGE_W, 12, "bar", fill="#FF9900", stroke="#FF9900", z=0))
    add(Box("title", "3차 프로젝트 AWS 전체 토폴로지", 38, 24, 1600, 62, "text", font_size=46, z=30))
    add(Box("subtitle", "Terraform Source · Foundation + Daily Runtime · Primary + Conditional DR · GitOps + Observability", 40, 88, 2100, 36, "text-muted", font_size=21, z=30))
    add(Box("legend-foundation", "Foundation", 2320, 28, 245, 60, "legend", stroke=C["foundation"], fill=C["foundation_fill"], font_size=20, z=30))
    add(Box("legend-daily", "Daily", 2580, 28, 190, 60, "legend", stroke=C["daily"], fill=C["daily_fill"], font_size=20, z=30))
    add(Box("legend-dr", "DR profile", 2785, 28, 230, 60, "legend", stroke=C["dr"], fill=C["dr_fill"], dashed=True, font_size=20, z=30))
    add(Box("legend-opt", "Opt-in", 3030, 28, 190, 60, "legend", stroke=C["opt"], fill=C["opt_fill"], dashed=True, font_size=20, z=30))
    add(Box("legend-layer", "Layer: Request ON", 3235, 28, 325, 60, "legend", stroke=C["request"], fill=C["white"], font_size=20, z=30))

    # External actors.
    add(Box("user", "사용자 / 실험자", 20, 250, 230, 140, "external", icon="user", stroke=C["line"], font_size=22, z=30))
    add(Box("github-repo", "GitHub Repo", 20, 560, 230, 125, "external", icon="source", stroke=C["line"], font_size=22, z=30))
    add(Box("github-actions", "GitHub Actions", 20, 705, 230, 125, "external", icon="source", stroke=C["deploy"], font_size=22, z=30))
    add(Box("operator", "운영자 PC\nTerraform · PowerShell", 20, 1010, 230, 155, "external", icon="toolkit", stroke=C["operations"], font_size=21, z=30))

    # AWS cloud and top shared areas.
    add(Box("aws-cloud", "AWS Cloud", 280, 135, 3280, 1715, "group", icon="cloud_group", stroke=C["ink"], fill="#FBFCFD", font_size=30, z=1))
    add(Box("global-foundation", "Global Edge · Persistent Foundation · Shared Control", 310, 170, 3220, 320, "group", parent="aws-cloud", stroke=C["foundation"], fill=C["foundation_fill"], font_size=28, z=2))
    add(Box("edge-area", "Request Entry", 335, 215, 1300, 245, "subgroup", parent="global-foundation", stroke=C["daily"], fill=C["daily_fill"], font_size=23, z=3))
    add(Box("platform-area", "Identity · Operations · Registry · Prerequisites", 1660, 215, 1845, 245, "subgroup", parent="global-foundation", stroke=C["foundation"], fill=C["white"], font_size=23, z=3))

    add(Box("route53", "Route 53\nDNS", 365, 260, 235, 175, "service", parent="edge-area", icon="route53", stroke=C["daily"], font_size=24, z=20))
    add(Box("acm", "ACM\nViewer TLS", 625, 260, 235, 175, "service", parent="edge-area", icon="acm", stroke=C["foundation"], font_size=24, z=20))
    add(Box("cloudfront", "CloudFront\nPrimary origin", 885, 260, 235, 175, "service", parent="edge-area", icon="cloudfront", stroke=C["daily"], font_size=24, z=20))
    add(Box("waf", "AWS WAF\nCOUNT", 1145, 260, 235, 175, "service", parent="edge-area", icon="waf", stroke=C["daily"], font_size=24, z=20))

    add(Box("iam", "IAM\nGitHub OIDC", 1685, 260, 235, 175, "service", parent="platform-area", icon="iam", stroke=C["foundation"], font_size=23, z=20))
    add(Box("ssm", "Systems Manager\nAdd-on install", 1940, 260, 235, 175, "service", parent="platform-area", icon="ssm", stroke=C["daily"], font_size=22, z=20))
    add(Box("ecr", "Amazon ECR\nImmutable image", 2195, 260, 235, 175, "service", parent="platform-area", icon="ecr", stroke=C["foundation"], font_size=22, z=20))
    add(Box("hosted-zone", "Existing Hosted Zone", 2450, 285, 235, 115, "chip", parent="platform-area", stroke=C["line"], fill=C["white"], font_size=21, z=20))
    add(Box("key-pair", "Existing EC2 Key Pair", 2705, 285, 235, 115, "chip", parent="platform-area", stroke=C["line"], fill=C["white"], font_size=20, z=20))
    add(Box("foundation-state", "Foundation State\nOutput Contract", 2960, 285, 260, 115, "chip", parent="platform-area", stroke=C["foundation"], fill=C["foundation_fill"], font_size=20, z=20))

    # Regions.
    add(Box("primary-region", "Primary · Seoul · ap-northeast-2", 310, 520, 1580, 980, "group", parent="aws-cloud", icon="region_group", stroke=C["network"], fill="#F9FDFD", font_size=30, z=2))
    add(Box("dr-region", "DR · Tokyo · ap-northeast-1", 1920, 520, 1580, 980, "group", parent="aws-cloud", icon="region_group", stroke=C["dr"], fill=C["dr_fill"], dashed=True, badge="DR profile", font_size=30, z=2))

    add(Box("p-app-s3", "Application S3\nPod access off", 1585, 550, 255, 135, "service-small", parent="primary-region", icon="s3", stroke=C["opt"], fill=C["white"], dashed=True, badge="OPT", font_size=20, z=20))
    add(Box("dr-app-s3", "Application S3\nCRR target", 3195, 550, 255, 135, "service-small", parent="dr-region", icon="s3", stroke=C["dr"], fill=C["white"], dashed=True, badge="DR", font_size=20, z=20))
    add(Box("dr-log-group", "DR DVWA Log Group", 2915, 570, 250, 95, "chip", parent="dr-region", stroke=C["foundation"], fill=C["foundation_fill"], font_size=19, z=20))

    add(Box("p-vpc", "Primary VPC · 10.0.0.0/16", 340, 690, 1520, 780, "group", parent="primary-region", icon="vpc_group", stroke=C["dr"], fill=C["white"], font_size=27, z=3))
    add(Box("dr-vpc", "DR VPC · 10.10.0.0/16", 1950, 690, 1520, 780, "group", parent="dr-region", icon="vpc_group", stroke=C["dr"], fill=C["white"], dashed=True, font_size=27, z=3))

    add(Box("p-igw", "Internet Gateway", 1005, 710, 190, 78, "resource", parent="p-vpc", icon="igw", stroke=C["dr"], font_size=18, z=20))
    add(Box("dr-igw", "Internet Gateway", 2615, 710, 190, 78, "resource", parent="dr-vpc", icon="igw", stroke=C["dr"], dashed=True, font_size=18, z=20))

    # AZ and subnet hierarchy.
    for region, offset, az1, az2, cidr in [
        ("p", 0, "2a", "2c", "10.0"),
        ("dr", 1610, "1a", "1c", "10.10"),
    ]:
        parent_vpc = "p-vpc" if region == "p" else "dr-vpc"
        stroke = C["line"] if region == "p" else C["dr"]
        dashed = region == "dr"
        add(Box(f"{region}-az-a", f"Availability Zone · {az1}", 370 + offset, 800, 710, 640, "az", parent=parent_vpc, stroke=stroke, fill="#FFFFFF", dashed=True, font_size=21, z=4))
        add(Box(f"{region}-az-c", f"Availability Zone · {az2}", 1120 + offset, 800, 710, 640, "az", parent=parent_vpc, stroke=stroke, fill="#FFFFFF", dashed=True, font_size=21, z=4))
        az_parent_a = f"{region}-az-a"
        az_parent_c = f"{region}-az-c"
        add(Box(f"{region}-public-a", f"Public · {cidr}.0.0/24", 390 + offset, 845, 670, 135, "subnet", parent=az_parent_a, icon="public_group", stroke=C["opt"], fill=C["public_fill"], font_size=18, z=5))
        add(Box(f"{region}-public-c", f"Public · {cidr}.1.0/24", 1140 + offset, 845, 670, 135, "subnet", parent=az_parent_c, icon="public_group", stroke=C["opt"], fill=C["public_fill"], font_size=18, z=5))
        add(Box(f"{region}-private-a", f"Private · {cidr}.10.0/24", 390 + offset, 995, 670, 275, "subnet", parent=az_parent_a, icon="private_group", stroke=C["network"], fill=C["private_fill"], font_size=18, z=5))
        add(Box(f"{region}-private-c", f"Private · {cidr}.11.0/24", 1140 + offset, 995, 670, 275, "subnet", parent=az_parent_c, icon="private_group", stroke=C["network"], fill=C["private_fill"], font_size=18, z=5))
        add(Box(f"{region}-data-a", f"Database · {cidr}.20.0/24", 390 + offset, 1285, 670, 130, "subnet", parent=az_parent_a, icon="private_group", stroke=C["dr"], fill=C["data_fill"], font_size=18, z=5))
        add(Box(f"{region}-data-c", f"Database · {cidr}.21.0/24", 1140 + offset, 1285, 670, 130, "subnet", parent=az_parent_c, icon="private_group", stroke=C["dr"], fill=C["data_fill"], font_size=18, z=5))

    # Public services.
    add(Box("p-bastion", "Bastion\nSSM + SSH", 445, 865, 190, 105, "resource", parent="p-az-a", icon="ec2", stroke=C["daily"], font_size=18, z=25))
    add(Box("p-nat", "NAT Gateway", 675, 865, 185, 105, "resource", parent="p-az-a", icon="nat", stroke=C["daily"], font_size=18, z=25))
    add(Box("p-alb", "ALB\n2 public subnets", 990, 850, 220, 125, "service-small", parent="p-vpc", icon="alb", stroke=C["daily"], font_size=19, z=25))
    add(Box("p-flow", "VPC REJECT Flow Logs", 1510, 875, 260, 80, "chip", parent="p-vpc", stroke=C["obs"], fill=C["obs_fill"], font_size=18, z=25))

    add(Box("dr-bastion", "Bastion\nSSM + SSH", 2055, 865, 190, 105, "resource", parent="dr-az-a", icon="ec2", stroke=C["dr"], dashed=True, badge="DR", font_size=18, z=25))
    add(Box("dr-nat", "NAT Gateway", 2285, 865, 185, 105, "resource", parent="dr-az-a", icon="nat", stroke=C["dr"], dashed=True, font_size=18, z=25))
    add(Box("dr-alb", "ALB\n2 public subnets", 2600, 850, 220, 125, "service-small", parent="dr-vpc", icon="alb", stroke=C["dr"], dashed=True, badge="DR", font_size=19, z=25))

    # EKS containers and internal components.
    add(Box("p-eks-box", "Amazon EKS · Private API · System + Workload", 410, 1005, 1370, 255, "eks-group", parent="p-vpc", icon="eks", stroke=C["daily"], fill="#FFFDFC", font_size=22, z=10))
    add(Box("dr-eks-box", "Amazon EKS · Private API · Profile", 2020, 1005, 1370, 255, "eks-group", parent="dr-vpc", icon="eks", stroke=C["dr"], fill=C["dr_fill"], dashed=True, badge="DR", font_size=22, z=10))

    add(Box("p-eks-api", "EKS\nControl Plane", 430, 1050, 175, 175, "service-small", parent="p-eks-box", icon="eks", stroke=C["daily"], font_size=19, z=25))
    add(Box("p-system-node", "Managed System Node", 630, 1060, 300, 72, "chip", parent="p-eks-box", stroke=C["daily"], fill=C["daily_fill"], font_size=19, z=25))
    add(Box("p-karpenter", "Karpenter · Workload Nodes", 955, 1060, 300, 72, "chip", parent="p-eks-box", stroke=C["daily"], fill=C["daily_fill"], font_size=18, z=25))
    add(Box("p-addons", "Add-ons · LBC · DNS · Fluent Bit", 1280, 1060, 465, 72, "chip", parent="p-eks-box", stroke=C["operations"], fill=C["private_fill"], font_size=18, z=25))
    add(Box("p-pod-identity", "EKS Pod Identity", 630, 1150, 300, 72, "chip", parent="p-eks-box", stroke=C["foundation"], fill=C["foundation_fill"], font_size=19, z=25))
    add(Box("p-argo", "Argo CD · in-cluster", 955, 1150, 300, 72, "chip", parent="p-eks-box", stroke=C["deploy"], fill="#F4FBF1", font_size=19, z=25))
    add(Box("p-dvwa", "BANK DVWA · Service + Pod", 1280, 1150, 465, 72, "chip", parent="p-eks-box", stroke=C["request"], fill=C["foundation_fill"], font_size=19, z=25))

    add(Box("dr-eks-api", "EKS\nControl Plane", 2040, 1050, 175, 175, "service-small", parent="dr-eks-box", icon="eks", stroke=C["dr"], dashed=True, font_size=19, z=25))
    add(Box("dr-system-node", "Managed System Node", 2240, 1060, 300, 72, "chip", parent="dr-eks-box", stroke=C["dr"], fill=C["dr_fill"], dashed=True, font_size=19, z=25))
    add(Box("dr-karpenter", "Karpenter · Workload Nodes", 2565, 1060, 300, 72, "chip", parent="dr-eks-box", stroke=C["dr"], fill=C["dr_fill"], dashed=True, font_size=18, z=25))
    add(Box("dr-addons", "Add-ons · LBC · DNS · Fluent Bit", 2890, 1060, 465, 72, "chip", parent="dr-eks-box", stroke=C["dr"], fill=C["dr_fill"], dashed=True, font_size=18, z=25))
    add(Box("dr-pod-identity", "EKS Pod Identity", 2240, 1150, 300, 72, "chip", parent="dr-eks-box", stroke=C["dr"], fill=C["dr_fill"], dashed=True, font_size=19, z=25))
    add(Box("dr-argo", "Argo CD · opt-in", 2565, 1150, 300, 72, "chip", parent="dr-eks-box", stroke=C["opt"], fill=C["opt_fill"], dashed=True, badge="OPT", font_size=19, z=25))
    add(Box("dr-dvwa", "DVWA · bootstrap 별도", 2890, 1150, 465, 72, "chip", parent="dr-eks-box", stroke=C["dr"], fill=C["white"], dashed=True, font_size=19, z=25))

    # Data services.
    add(Box("p-rds", "RDS MariaDB\nSingle / Multi-AZ", 500, 1295, 280, 125, "service-small", parent="p-vpc", icon="rds", stroke=C["daily"], font_size=19, z=25))
    add(Box("p-valkey", "Valkey\nIndependent · opt-in", 910, 1295, 280, 125, "service-small", parent="p-vpc", icon="valkey", stroke=C["opt"], dashed=True, badge="OPT", font_size=18, z=25))
    add(Box("p-efs", "EFS\n2 mount targets", 1320, 1295, 280, 125, "service-small", parent="p-vpc", icon="efs", stroke=C["opt"], dashed=True, badge="OPT", font_size=18, z=25))

    add(Box("dr-rds", "RDS Read Replica\nCross-Region", 2110, 1295, 280, 125, "service-small", parent="dr-vpc", icon="rds", stroke=C["dr"], dashed=True, badge="DR", font_size=18, z=25))
    add(Box("dr-valkey", "Valkey\nIndependent · opt-in", 2520, 1295, 280, 125, "service-small", parent="dr-vpc", icon="valkey", stroke=C["opt"], dashed=True, badge="OPT", font_size=18, z=25))
    add(Box("dr-efs", "EFS\nIndependent · opt-in", 2930, 1295, 280, 125, "service-small", parent="dr-vpc", icon="efs", stroke=C["opt"], dashed=True, badge="OPT", font_size=18, z=25))

    # Observability domains.
    add(Box("observability", "Observability · Detection · Query", 310, 1530, 3220, 285, "group", parent="aws-cloud", stroke=C["obs"], fill=C["obs_fill"], font_size=28, z=2))
    add(Box("audit-area", "Audit & Storage", 340, 1580, 900, 205, "subgroup", parent="observability", stroke=C["foundation"], fill=C["white"], font_size=22, z=3))
    add(Box("detect-area", "Detection & Alert", 1270, 1580, 1160, 205, "subgroup", parent="observability", stroke=C["obs"], fill=C["white"], font_size=22, z=3))
    add(Box("query-area", "Query & Review", 2460, 1580, 1040, 205, "subgroup", parent="observability", stroke=C["operations"], fill=C["white"], font_size=22, z=3))

    add(Box("cloudtrail", "CloudTrail", 365, 1625, 240, 140, "service-small", parent="audit-area", icon="cloudtrail", stroke=C["foundation"], font_size=20, z=25))
    add(Box("cloudwatch", "CloudWatch Logs", 650, 1625, 240, 140, "service-small", parent="audit-area", icon="cloudwatch", stroke=C["foundation"], font_size=19, z=25))
    add(Box("security-s3", "Security Log S3\n30 days", 935, 1625, 240, 140, "service-small", parent="audit-area", icon="s3", stroke=C["foundation"], font_size=18, z=25))

    add(Box("guardduty", "GuardDuty\nPrimary", 1295, 1625, 240, 140, "service-small", parent="detect-area", icon="guardduty", stroke=C["foundation"], font_size=19, z=25))
    add(Box("eventbridge", "EventBridge", 1565, 1625, 240, 140, "service-small", parent="detect-area", icon="eventbridge", stroke=C["foundation"], font_size=19, z=25))
    add(Box("alarm", "Metric Filter\n+ Alarm", 1835, 1635, 240, 120, "chip", parent="detect-area", stroke=C["obs"], fill=C["obs_fill"], font_size=19, z=25))
    add(Box("sns", "Amazon SNS", 2105, 1625, 240, 140, "service-small", parent="detect-area", icon="sns", stroke=C["foundation"], font_size=19, z=25))

    add(Box("logs-insights", "CloudWatch\nLogs Insights", 2485, 1635, 280, 120, "chip", parent="query-area", stroke=C["operations"], fill=C["private_fill"], font_size=19, z=25))
    add(Box("athena", "Athena + Glue", 2795, 1625, 250, 140, "service-small", parent="query-area", icon="athena", stroke=C["foundation"], font_size=19, z=25))
    add(Box("security-review", "Security Window\nReview", 3075, 1635, 370, 120, "chip", parent="query-area", stroke=C["operations"], fill=C["private_fill"], font_size=19, z=25))

    # Local response tools are intentionally outside the AWS Cloud boundary.
    add(Box("local-tools", "AWS 외부 · Local Response & Evidence", 610, 1880, 2590, 250, "group", stroke=C["line"], fill=C["white"], dashed=True, font_size=27, z=2))
    add(Box("grafana", "Local Grafana\nAthena / S3", 820, 1940, 440, 145, "external", icon="server", parent="local-tools", stroke=C["operations"], font_size=21, z=25))
    add(Box("waf-viewer", "WAF Live Viewer\nCloudWatch Live Tail", 1335, 1940, 440, 145, "external", icon="toolkit", parent="local-tools", stroke=C["obs"], font_size=21, z=25))
    add(Box("evidence", "Evidence Bundle\nSanitized · SHA-256", 1850, 1940, 440, 145, "external", icon="source", parent="local-tools", stroke=C["foundation"], font_size=21, z=25))
    add(Box("runtime-note", "Source topology · 실제 Runtime 활성 상태는 별도 검증", 2365, 1955, 620, 115, "chip", parent="local-tools", stroke=C["line"], fill=C["bg"], font_size=20, z=25))


def build_edges() -> None:
    # Request flow: visible by default.
    edge("req-1", "user", "route53", "layer-request", C["request"], label="DNS", width=5)
    edge("req-2", "route53", "cloudfront", "layer-request", C["request"], label="Alias", width=5)
    edge("req-3", "acm", "cloudfront", "layer-request", C["request"], label="TLS", dashed=True, width=3, exit_xy=(0.5, 1.0), entry_xy=(0.5, 0.0))
    edge("req-4", "waf", "cloudfront", "layer-request", C["request"], label="Web ACL", dashed=True, width=3, exit_xy=(0.0, 0.5), entry_xy=(1.0, 0.5))
    edge("req-5", "cloudfront", "p-alb", "layer-request", C["request"], label="HTTP :80", width=5, exit_xy=(0.5, 1.0), entry_xy=(0.5, 0.0), points=[(1000, 505), (1100, 505), (1100, 830)])
    edge("req-6", "p-alb", "p-dvwa", "layer-request", C["request"], label="Pod IP :80", width=5, exit_xy=(0.5, 1.0), entry_xy=(0.5, 0.0))
    edge("req-7", "p-dvwa", "p-rds", "layer-request", C["request"], label="MariaDB", width=5, exit_xy=(0.5, 1.0), entry_xy=(0.5, 0.0), points=[(1510, 1275), (640, 1275)])

    # GitOps delivery.
    edge("dep-1", "github-repo", "github-actions", "layer-deployment", C["deploy"], label="Push")
    edge("dep-2", "github-actions", "iam", "layer-deployment", C["deploy"], label="OIDC")
    edge("dep-3", "iam", "ecr", "layer-deployment", C["deploy"], label="Push role")
    edge("dep-4", "github-actions", "ecr", "layer-deployment", C["deploy"], label="sha image")
    edge("dep-5", "github-actions", "github-repo", "layer-deployment", C["deploy"], label="values.yaml", dashed=True, exit_xy=(0.0, 0.4), entry_xy=(0.0, 0.6), points=[(5, 760), (5, 620)])
    edge("dep-6", "github-repo", "p-argo", "layer-deployment", C["deploy"], label="Git desired state")
    edge("dep-7", "p-argo", "p-dvwa", "layer-deployment", C["deploy"], label="Sync")
    edge("dep-8", "ecr", "p-dvwa", "layer-deployment", C["deploy"], label="Image pull", dashed=True)

    # Operations and bootstrap.
    edge("ops-1", "operator", "ssm", "layer-operations", C["operations"], label="Association", dashed=True)
    edge("ops-2", "ssm", "p-bastion", "layer-operations", C["operations"], label="Run Command", dashed=True)
    edge("ops-3", "operator", "p-bastion", "layer-operations", C["operations"], label="SSH / SCP")
    edge("ops-4", "key-pair", "p-bastion", "layer-operations", C["operations"], label="Key", dashed=True)
    edge("ops-5", "p-bastion", "p-eks-api", "layer-operations", C["operations"], label="kubectl / Helm")
    edge("ops-6", "p-bastion", "p-rds", "layer-operations", C["operations"], label="DB bootstrap", dashed=True)
    edge("ops-7", "ssm", "dr-bastion", "layer-operations", C["operations"], label="Run Command", dashed=True)
    edge("ops-8", "operator", "dr-bastion", "layer-operations", C["operations"], label="DR ops", dashed=True)
    edge("ops-9", "key-pair", "dr-bastion", "layer-operations", C["operations"], label="Key", dashed=True)
    edge("ops-10", "dr-bastion", "dr-eks-api", "layer-operations", C["operations"], label="kubectl / Helm")

    # DR relationships.
    edge("dr-1", "p-rds", "dr-rds", "layer-dr", C["replication"], label="Cross-Region replica", dashed=True, width=5)
    edge("dr-2", "p-app-s3", "dr-app-s3", "layer-dr", C["replication"], label="S3 CRR", dashed=True, width=5)
    edge("dr-3", "dr-alb", "dr-dvwa", "layer-dr", C["dr"], label="Conditional :80", dashed=True)

    # Observability, detection, query and response.
    edge("obs-1", "waf", "cloudwatch", "layer-observability", C["telemetry"], label="WAF logs", dashed=True)
    edge("obs-2", "cloudfront", "security-s3", "layer-observability", C["telemetry"], label="Access logs", dashed=True)
    edge("obs-3", "p-alb", "security-s3", "layer-observability", C["telemetry"], label="ALB logs", dashed=True)
    edge("obs-4", "p-flow", "security-s3", "layer-observability", C["telemetry"], label="REJECT logs", dashed=True)
    edge("obs-5", "p-eks-api", "cloudwatch", "layer-observability", C["telemetry"], label="Control plane", dashed=True)
    edge("obs-6", "p-dvwa", "cloudwatch", "layer-observability", C["telemetry"], label="Fluent Bit", dashed=True)
    edge("obs-7", "dr-log-group", "cloudwatch", "layer-observability", C["telemetry"], label="DR logs", dashed=True)
    edge("obs-8", "cloudtrail", "cloudwatch", "layer-observability", C["telemetry"], label="Events")
    edge("obs-9", "cloudtrail", "security-s3", "layer-observability", C["telemetry"], label="Archive")
    edge("obs-10", "guardduty", "eventbridge", "layer-observability", C["telemetry"], label="Finding")
    edge("obs-11", "eventbridge", "cloudwatch", "layer-observability", C["telemetry"], label="Original")
    edge("obs-12", "eventbridge", "sns", "layer-observability", C["telemetry"], label="Alert")
    edge("obs-13", "cloudwatch", "alarm", "layer-observability", C["telemetry"], label="Metric")
    edge("obs-14", "alarm", "sns", "layer-observability", C["telemetry"], label="Notify")
    edge("obs-15", "cloudwatch", "logs-insights", "layer-observability", C["operations"], label="Query")
    edge("obs-16", "security-s3", "athena", "layer-observability", C["operations"], label="SQL")
    edge("obs-17", "athena", "grafana", "layer-observability", C["operations"], label="Dashboard")
    edge("obs-18", "cloudwatch", "waf-viewer", "layer-observability", C["operations"], label="Live Tail")
    edge("obs-19", "logs-insights", "security-review", "layer-observability", C["operations"], label="Review")
    edge("obs-20", "athena", "security-review", "layer-observability", C["operations"], label="Review")
    edge("obs-21", "security-review", "evidence", "layer-observability", C["operations"], label="Sanitized evidence")


def verify_assets() -> None:
    missing = [f"{key}: {path}" for key, path in ICON_PATHS.items() if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing AWS icon assets:\n" + "\n".join(missing))


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_BOLD if bold else FONT_REGULAR), size)


def rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


def draw_dashed_rectangle(draw: ImageDraw.ImageDraw, xy: tuple[int, int, int, int], fill: str, outline: str, width: int = 3, dash: int = 12, gap: int = 8, radius: int = 12) -> None:
    x1, y1, x2, y2 = xy
    draw.rounded_rectangle(xy, radius=radius, fill=fill)
    for x in range(x1 + radius, x2 - radius, dash + gap):
        draw.line((x, y1, min(x + dash, x2 - radius), y1), fill=outline, width=width)
        draw.line((x, y2, min(x + dash, x2 - radius), y2), fill=outline, width=width)
    for y in range(y1 + radius, y2 - radius, dash + gap):
        draw.line((x1, y, x1, min(y + dash, y2 - radius)), fill=outline, width=width)
        draw.line((x2, y, x2, min(y + dash, y2 - radius)), fill=outline, width=width)


def paste_icon(canvas: Image.Image, key: str, x: int, y: int, size: int) -> None:
    icon = Image.open(ICON_PATHS[key]).convert("RGBA")
    icon.thumbnail((size, size), Image.Resampling.LANCZOS)
    px = x + (size - icon.width) // 2
    py = y + (size - icon.height) // 2
    canvas.alpha_composite(icon, (px, py))


def centered_text(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], text: str, size: int, *, bold: bool = True, color: str = C["ink"], spacing: int = 4) -> None:
    x1, y1, x2, y2 = box
    f = font(size, bold)
    bounds = draw.multiline_textbbox((0, 0), text, font=f, spacing=spacing, align="center")
    w = bounds[2] - bounds[0]
    h = bounds[3] - bounds[1]
    draw.multiline_text(((x1 + x2 - w) / 2, (y1 + y2 - h) / 2), text, font=f, fill=color, spacing=spacing, align="center")


def render_box(canvas: Image.Image, box: Box) -> None:
    draw = ImageDraw.Draw(canvas)
    xy = (box.x, box.y, box.x + box.w, box.y + box.h)
    if box.kind == "bar":
        draw.rectangle(xy, fill=box.fill)
        return
    if box.kind in {"text", "text-muted"}:
        draw.text((box.x, box.y), box.label, font=font(box.font_size, box.kind == "text"), fill=C["ink"] if box.kind == "text" else C["muted"])
        return

    radius = 18 if box.kind in {"service", "service-small", "external", "legend", "chip", "resource"} else 8
    if box.dashed:
        draw_dashed_rectangle(draw, xy, box.fill, box.stroke, width=3, radius=radius)
    else:
        width = 4 if box.kind in {"group", "eks-group"} else 2
        draw.rounded_rectangle(xy, radius=radius, fill=box.fill, outline=box.stroke, width=width)

    if box.kind in {"group", "subgroup", "az", "subnet", "eks-group"}:
        icon_size = 34 if box.kind != "subnet" else 28
        title_x = box.x + 18
        if box.icon:
            paste_icon(canvas, box.icon, box.x + 14, box.y + 10, icon_size)
            title_x = box.x + 20 + icon_size
        draw.text((title_x, box.y + 12), box.label, font=font(box.font_size, True), fill=box.stroke if box.kind in {"group", "eks-group"} else C["ink"])
    elif box.kind in {"service", "service-small", "resource", "external"}:
        icon_size = 88 if box.kind == "service" else 64 if box.kind in {"service-small", "external"} else 48
        if box.icon:
            paste_icon(canvas, box.icon, box.x + (box.w - icon_size) // 2, box.y + 8, icon_size)
        label_top = box.y + icon_size + 16 if box.icon else box.y + 10
        centered_text(draw, (box.x + 5, label_top, box.x + box.w - 5, box.y + box.h - 5), box.label, box.font_size, bold=True, spacing=2)
    else:
        centered_text(draw, xy, box.label, box.font_size, bold=True)

    if box.badge:
        badge_w = max(56, len(box.badge) * 14 + 22)
        bx1 = box.x + box.w - badge_w - 8
        by1 = box.y + 8
        draw.rounded_rectangle((bx1, by1, bx1 + badge_w, by1 + 34), radius=17, fill=box.stroke)
        centered_text(draw, (bx1, by1, bx1 + badge_w, by1 + 34), box.badge, 15, color=C["white"])


def dashed_polyline(draw: ImageDraw.ImageDraw, points: list[tuple[int, int]], fill: str, width: int, dash: int = 14, gap: int = 10) -> None:
    for a, b in zip(points, points[1:]):
        x1, y1 = a
        x2, y2 = b
        distance = math.hypot(x2 - x1, y2 - y1)
        if distance == 0:
            continue
        ux = (x2 - x1) / distance
        uy = (y2 - y1) / distance
        pos = 0.0
        while pos < distance:
            end = min(pos + dash, distance)
            draw.line((x1 + ux * pos, y1 + uy * pos, x1 + ux * end, y1 + uy * end), fill=fill, width=width)
            pos += dash + gap


def arrowhead(draw: ImageDraw.ImageDraw, a: tuple[int, int], b: tuple[int, int], color: str, size: int = 16) -> None:
    dx = b[0] - a[0]
    dy = b[1] - a[1]
    length = math.hypot(dx, dy)
    if not length:
        return
    ux, uy = dx / length, dy / length
    px, py = -uy, ux
    p1 = (b[0] - ux * size + px * size * 0.55, b[1] - uy * size + py * size * 0.55)
    p2 = (b[0] - ux * size - px * size * 0.55, b[1] - uy * size - py * size * 0.55)
    draw.polygon((b, p1, p2), fill=color)


def edge_points(item: Edge, by_id: dict[str, Box]) -> list[tuple[int, int]]:
    source = by_id[item.source]
    target = by_id[item.target]
    start = (int(source.x + source.w * item.exit_xy[0]), int(source.y + source.h * item.exit_xy[1]))
    end = (int(target.x + target.w * item.entry_xy[0]), int(target.y + target.h * item.entry_xy[1]))
    if item.points:
        return [start, *item.points, end]
    if abs(start[0] - end[0]) >= abs(start[1] - end[1]):
        mid_x = (start[0] + end[0]) // 2
        return [start, (mid_x, start[1]), (mid_x, end[1]), end]
    mid_y = (start[1] + end[1]) // 2
    return [start, (start[0], mid_y), (end[0], mid_y), end]


def render_preview(path: Path, visible_layers: set[str]) -> None:
    canvas = Image.new("RGBA", (PAGE_W, PAGE_H), rgb(C["bg"]) + (255,))
    by_id = {box.box_id: box for box in BOXES}
    for box in sorted(BOXES, key=lambda value: value.z):
        render_box(canvas, box)

    draw = ImageDraw.Draw(canvas)
    for item in EDGES:
        if item.layer not in visible_layers:
            continue
        pts = edge_points(item, by_id)
        if item.dashed:
            dashed_polyline(draw, pts, item.color, item.width)
        else:
            draw.line(pts, fill=item.color, width=item.width, joint="curve")
        arrowhead(draw, pts[-2], pts[-1], item.color, max(14, item.width * 4))
        if item.label:
            mid = pts[len(pts) // 2]
            bounds = draw.textbbox((0, 0), item.label, font=font(16, True))
            tw = bounds[2] - bounds[0]
            th = bounds[3] - bounds[1]
            draw.rounded_rectangle((mid[0] - tw / 2 - 6, mid[1] - th / 2 - 4, mid[0] + tw / 2 + 6, mid[1] + th / 2 + 4), radius=5, fill=C["white"])
            draw.text((mid[0] - tw / 2, mid[1] - th / 2), item.label, font=font(16, True), fill=item.color)

    path.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(path, quality=96)


def image_style(key: str, image_w: int, image_h: int, stroke: str, fill: str, font_size: int, dashed: bool = False) -> str:
    data = base64.b64encode(ICON_PATHS[key].read_bytes()).decode("ascii")
    style = (
        "shape=label;rounded=1;arcSize=12;whiteSpace=wrap;html=1;"
        f"image=data:image/png,{data};imageWidth={image_w};imageHeight={image_h};"
        "imageAlign=center;imageVerticalAlign=top;align=center;verticalAlign=bottom;"
        "spacingTop=8;spacingBottom=7;spacingLeft=5;spacingRight=5;"
        f"fillColor={fill};strokeColor={stroke};strokeWidth=2;"
        f"fontFamily=Malgun Gothic;fontSize={font_size};fontStyle=1;shadow=0;"
    )
    if dashed:
        style += "dashed=1;dashPattern=10 8;"
    return style


def group_style(box: Box) -> str:
    style = (
        "shape=label;container=1;collapsible=0;recursiveResize=0;rounded=0;"
        "whiteSpace=wrap;html=1;align=left;verticalAlign=top;"
        "spacingTop=11;spacingLeft=54;spacingRight=8;"
        f"fillColor={box.fill};strokeColor={box.stroke};strokeWidth=3;"
        f"fontFamily=Malgun Gothic;fontSize={box.font_size};fontStyle=1;shadow=0;"
    )
    if box.icon:
        data = base64.b64encode(ICON_PATHS[box.icon].read_bytes()).decode("ascii")
        style += f"image=data:image/png,{data};imageWidth=34;imageHeight=34;imageAlign=left;imageVerticalAlign=top;"
    if box.dashed:
        style += "dashed=1;dashPattern=10 8;"
    return style


def box_style(box: Box) -> str:
    if box.kind in {"group", "subgroup", "az", "subnet", "eks-group"}:
        return group_style(box)
    if box.kind in {"service", "service-small", "resource", "external"} and box.icon:
        if box.kind == "service":
            iw, ih = 88, 88
        elif box.kind in {"service-small", "external"}:
            iw, ih = 64, 64
        else:
            iw, ih = 48, 48
        return image_style(box.icon, iw, ih, box.stroke, box.fill, box.font_size, box.dashed)
    if box.kind == "bar":
        return f"rounded=0;fillColor={box.fill};strokeColor={box.stroke};"
    if box.kind in {"text", "text-muted"}:
        color = C["ink"] if box.kind == "text" else C["muted"]
        bold = 1 if box.kind == "text" else 0
        return f"text;html=1;align=left;verticalAlign=middle;fontFamily=Malgun Gothic;fontSize={box.font_size};fontStyle={bold};fontColor={color};strokeColor=none;fillColor=none;"
    style = (
        "rounded=1;arcSize=12;whiteSpace=wrap;html=1;align=center;verticalAlign=middle;"
        f"fillColor={box.fill};strokeColor={box.stroke};strokeWidth=2;"
        f"fontFamily=Malgun Gothic;fontSize={box.font_size};fontStyle=1;shadow=0;"
    )
    if box.dashed:
        style += "dashed=1;dashPattern=10 8;"
    return style


def html_value(box: Box) -> str:
    lines = box.label.split("\n")
    if box.kind in {"service", "service-small", "resource", "external"} and len(lines) > 1:
        title = html.escape(lines[0])
        subtitle = html.escape(" · ".join(lines[1:]))
        return f'<div style="text-align:center;line-height:1.18;"><b>{title}</b><br><span style="font-size:{max(14, box.font_size - 4)}px;color:{C["muted"]};font-weight:400;">{subtitle}</span></div>'
    return "<br>".join(html.escape(line) for line in lines)


def add_vertex(root: ET.Element, box: Box, by_id: dict[str, Box]) -> None:
    attrs = {
        "id": box.box_id,
        "value": html_value(box),
        "style": box_style(box),
        "vertex": "1",
        "parent": box.parent,
        "dataKind": box.kind,
    }
    attrs.update(box.metadata)
    if box.badge:
        attrs["dataBadge"] = box.badge
    cell = ET.SubElement(root, "mxCell", attrs)
    x, y = box.x, box.y
    if box.parent in by_id:
        parent = by_id[box.parent]
        x -= parent.x
        y -= parent.y
    ET.SubElement(cell, "mxGeometry", {"x": str(x), "y": str(y), "width": str(box.w), "height": str(box.h), "as": "geometry"})


def add_drawio_edge(root: ET.Element, item: Edge) -> None:
    style = (
        "edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;"
        f"strokeWidth={item.width};strokeColor={item.color};endArrow=block;endFill=1;"
        f"fontFamily=Malgun Gothic;fontSize=16;fontStyle=1;labelBackgroundColor={C['white']};"
        f"exitX={item.exit_xy[0]};exitY={item.exit_xy[1]};entryX={item.entry_xy[0]};entryY={item.entry_xy[1]};exitDx=0;exitDy=0;entryDx=0;entryDy=0;"
    )
    if item.dashed:
        style += "dashed=1;dashPattern=10 8;"
    cell = ET.SubElement(
        root,
        "mxCell",
        {
            "id": item.edge_id,
            "value": item.label,
            "style": style,
            "edge": "1",
            "parent": item.layer,
            "source": item.source,
            "target": item.target,
            "dataFlow": item.layer.replace("layer-", ""),
        },
    )
    geometry = ET.SubElement(cell, "mxGeometry", {"relative": "1", "as": "geometry"})
    if item.points:
        arr = ET.SubElement(geometry, "Array", {"as": "points"})
        for x, y in item.points:
            ET.SubElement(arr, "mxPoint", {"x": str(x), "y": str(y)})


def write_drawio(path: Path) -> None:
    mxfile = ET.Element(
        "mxfile",
        {
            "host": "app.diagrams.net",
            "modified": "2026-08-11T00:00:00.000Z",
            "agent": "Codex",
            "version": "24.7.17",
            "type": "device",
            "compressed": "false",
        },
    )
    diagram = ET.SubElement(mxfile, "diagram", {"name": "09 · FULL TOPOLOGY · LAYERS", "id": "mentor-full-topology-v9"})
    model = ET.SubElement(
        diagram,
        "mxGraphModel",
        {
            "dx": "1600",
            "dy": "900",
            "grid": "1",
            "gridSize": "10",
            "guides": "1",
            "tooltips": "1",
            "connect": "1",
            "arrows": "1",
            "fold": "1",
            "page": "1",
            "pageScale": "1",
            "pageWidth": str(PAGE_W),
            "pageHeight": str(PAGE_H),
            "math": "0",
            "shadow": "0",
        },
    )
    root = ET.SubElement(model, "root")
    ET.SubElement(root, "mxCell", {"id": "0"})
    layers = [
        ("layer-topology", "00 · Full Topology", True),
        ("layer-request", "01 · Request", True),
        ("layer-deployment", "02 · Deployment", False),
        ("layer-operations", "03 · Operations", False),
        ("layer-dr", "04 · DR", False),
        ("layer-observability", "05 · Observability", False),
    ]
    for layer_id, name, visible in layers:
        attrs = {"id": layer_id, "value": name, "parent": "0"}
        if not visible:
            attrs["visible"] = "0"
        ET.SubElement(root, "mxCell", attrs)

    by_id = {box.box_id: box for box in BOXES}
    for box in BOXES:
        add_vertex(root, box, by_id)
    for item in EDGES:
        add_drawio_edge(root, item)

    ET.indent(mxfile, space="  ")
    path.write_text('<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(mxfile, encoding="unicode"), encoding="utf-8", newline="\n")


def validate_model() -> None:
    ids = [box.box_id for box in BOXES]
    duplicates = sorted({value for value in ids if ids.count(value) > 1})
    if duplicates:
        raise ValueError(f"Duplicate box IDs: {duplicates}")
    id_set = set(ids)
    missing_targets = sorted({value for item in EDGES for value in (item.source, item.target) if value not in id_set})
    if missing_targets:
        raise ValueError(f"Missing edge endpoints: {missing_targets}")
    required = {
        "route53", "acm", "cloudfront", "waf", "iam", "ssm", "ecr",
        "primary-region", "dr-region", "p-vpc", "dr-vpc", "p-bastion", "dr-bastion",
        "p-alb", "dr-alb", "p-eks-api", "dr-eks-api", "p-pod-identity", "dr-pod-identity",
        "p-rds", "dr-rds", "p-valkey", "dr-valkey", "p-efs", "dr-efs", "p-app-s3", "dr-app-s3",
        "cloudtrail", "guardduty", "eventbridge", "sns", "cloudwatch", "security-s3", "athena",
        "grafana", "waf-viewer", "evidence", "p-karpenter", "dr-karpenter", "p-argo", "dr-argo", "p-dvwa", "dr-dvwa",
    }
    missing = sorted(required - id_set)
    if missing:
        raise ValueError(f"Required topology nodes missing: {missing}")
    for box in BOXES:
        if box.x < 0 or box.y < 0 or box.x + box.w > PAGE_W or box.y + box.h > PAGE_H:
            raise ValueError(f"Out-of-page box: {box.box_id}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--drawio", type=Path, default=HERE / "09_MENTOR_FULL_TOPOLOGY__ZOOMABLE_LAYERS__v9.drawio")
    parser.add_argument("--preview-dir", type=Path)
    args = parser.parse_args()

    verify_assets()
    build_boxes()
    build_edges()
    validate_model()
    write_drawio(args.drawio)
    print(args.drawio)

    if args.preview_dir:
        previews = {
            "overview": {"layer-request"},
            "deployment": {"layer-deployment"},
            "operations": {"layer-operations"},
            "dr": {"layer-dr"},
            "observability": {"layer-observability"},
        }
        for name, layers in previews.items():
            output = args.preview_dir / f"v9-{name}.png"
            render_preview(output, layers)
            print(output)


if __name__ == "__main__":
    main()
