from __future__ import annotations

import argparse
import base64
import html
import math
import xml.etree.ElementTree as ET
from dataclasses import replace
from pathlib import Path

from PIL import Image, ImageDraw

import generate_mentor_full_topology_v9 as base


HERE = Path(__file__).resolve().parent
PAGE_W = 4000
PAGE_H = 2300


def add_box(
    box_id: str,
    label: str,
    x: int,
    y: int,
    w: int,
    h: int,
    kind: str,
    *,
    parent: str = "layer-topology",
    icon: str | None = None,
    stroke: str = base.C["border"],
    fill: str = base.C["white"],
    dashed: bool = False,
    badge: str | None = None,
    font_size: int = 24,
    z: int = 20,
    display: str = "",
) -> None:
    base.add(
        base.Box(
            box_id,
            label,
            x,
            y,
            w,
            h,
            kind,
            parent=parent,
            icon=icon,
            stroke=stroke,
            fill=fill,
            dashed=dashed,
            badge=badge,
            font_size=font_size,
            z=z,
            metadata={"dataDisplay": display} if display else {},
        )
    )


def build_boxes() -> None:
    C = base.C

    # Page header and compact state legend.
    add_box("header-accent", "", 0, 0, PAGE_W, 12, "bar", fill="#FF9900", stroke="#FF9900", z=0)
    add_box("title", "3차 프로젝트 AWS 전체 인프라", 38, 22, 1800, 58, "text", font_size=44, z=40)
    add_box("subtitle", "Terraform Source · Shared Edge · Primary + DR · GitOps · Detection & Response", 40, 78, 2100, 34, "text-muted", font_size=21, z=40)
    add_box("legend-foundation", "Foundation", 2470, 28, 240, 58, "legend", stroke=C["foundation"], fill=C["foundation_fill"], font_size=20, z=40)
    add_box("legend-daily", "Daily", 2730, 28, 190, 58, "legend", stroke=C["daily"], fill=C["daily_fill"], font_size=20, z=40)
    add_box("legend-dr", "DR profile", 2940, 28, 235, 58, "legend", stroke=C["dr"], fill=C["dr_fill"], dashed=True, font_size=20, z=40)
    add_box("legend-opt", "Opt-in", 3195, 28, 190, 58, "legend", stroke=C["opt"], fill=C["opt_fill"], dashed=True, font_size=20, z=40)
    add_box("legend-layer", "Summary flow", 3405, 28, 300, 58, "legend", stroke=C["request"], fill="#FFFFFF", font_size=20, z=40)

    # External inputs form one horizontal shelf instead of a left-side rail.
    add_box("user", "사용자 / 실험자", 1250, 155, 230, 110, "external", icon="user", stroke=C["line"], font_size=22, z=35)
    add_box("github-repo", "GitHub Repo", 250, 155, 230, 110, "external", icon="source", stroke=C["line"], font_size=22, z=35)
    add_box("github-actions", "GitHub Actions", 520, 155, 230, 110, "external", icon="source", stroke=C["deploy"], font_size=22, z=35)
    add_box("operator", "운영자 PC\nTerraform · PowerShell", 2860, 145, 250, 125, "external", icon="toolkit", stroke=C["operations"], font_size=21, z=35)

    # Shared AWS area. Service icons are free-standing, matching the chosen reference grammar.
    add_box("aws-cloud", "AWS Cloud", 100, 300, 3800, 1780, "group", icon="cloud_group", stroke=C["ink"], fill="#FBFCFD", font_size=32, z=1)
    add_box("global-foundation", "Shared Edge · Identity · Operations · Prerequisites", 150, 340, 3700, 275, "group", parent="aws-cloud", stroke=C["foundation"], fill=C["foundation_fill"], font_size=30, z=2)
    add_box("edge-area", "Request Entry", 190, 390, 2200, 190, "rail", parent="global-foundation", stroke=C["daily"], fill=C["foundation_fill"], font_size=24, z=3)
    add_box("platform-area", "Shared Control", 2440, 390, 1370, 190, "rail", parent="global-foundation", stroke=C["foundation"], fill=C["foundation_fill"], font_size=24, z=3)

    add_box("route53", "Route 53\nDNS", 1220, 405, 210, 165, "free-service", parent="edge-area", icon="route53", stroke=C["foundation"], font_size=25, z=25)
    add_box("cloudfront", "CloudFront\nPrimary origin", 1480, 405, 220, 165, "free-service", parent="edge-area", icon="cloudfront", stroke=C["foundation"], font_size=24, z=25)
    add_box("acm", "ACM\nTLS", 1740, 405, 200, 165, "free-service", parent="edge-area", icon="acm", stroke=C["obs"], dashed=True, badge="OPT", font_size=25, z=25)
    add_box("waf", "AWS WAF\nCOUNT", 1980, 405, 210, 165, "free-service", parent="edge-area", icon="waf", stroke=C["obs"], font_size=25, z=25)

    add_box("iam", "IAM\nGitHub OIDC", 2490, 405, 210, 165, "free-service", parent="platform-area", icon="iam", stroke=C["foundation"], font_size=24, z=25)
    add_box("ssm", "Systems Manager\nAdd-ons", 2730, 405, 220, 165, "free-service", parent="platform-area", icon="ssm", stroke=C["operations"], font_size=23, z=25)
    add_box("hosted-zone", "Hosted Zone", 2980, 450, 230, 82, "micro", parent="platform-area", stroke=C["line"], fill="#FFFFFF", font_size=20, z=25)
    add_box("key-pair", "EC2 Key Pair", 3240, 450, 230, 82, "micro", parent="platform-area", stroke=C["line"], fill="#FFFFFF", font_size=20, z=25)
    add_box("foundation-state", "Foundation State\nOutput Contract", 3500, 435, 260, 110, "micro", parent="platform-area", stroke=C["foundation"], fill=C["foundation_fill"], font_size=20, z=25)

    # Equal region columns with a dedicated cross-region gutter between them.
    add_box("primary-region", "Primary · Seoul · ap-northeast-2", 150, 650, 1770, 975, "group", parent="aws-cloud", icon="region_group", stroke=C["network"], fill="#FFFFFF", font_size=32, z=2)
    add_box("dr-region", "DR · Tokyo · ap-northeast-1", 2080, 650, 1770, 975, "group", parent="aws-cloud", icon="region_group", stroke=C["dr"], fill="#FFFFFF", dashed=True, badge="DR profile", font_size=32, z=2)

    # Regional services align toward the center gutter, as in the selected reference.
    add_box("ecr", "Amazon ECR\nImmutable image", 300, 700, 240, 145, "free-small", parent="primary-region", icon="ecr", stroke=C["foundation"], font_size=24, z=25)
    add_box("p-app-s3", "Application S3\nAccess opt-in", 1580, 700, 240, 145, "free-small", parent="primary-region", icon="s3", stroke=C["opt"], dashed=True, badge="OPT", font_size=23, z=25)
    add_box("dr-app-s3", "Application S3\nCRR target", 2110, 700, 240, 145, "free-small", parent="dr-region", icon="s3", stroke=C["dr"], dashed=True, badge="DR", font_size=23, z=25)
    add_box("dr-log-group", "DR DVWA Log Group", 3160, 735, 430, 76, "micro", parent="dr-region", stroke=C["foundation"], fill=C["foundation_fill"], font_size=20, z=25)

    add_box("p-vpc", "Primary VPC · 10.0.0.0/16", 190, 850, 1690, 730, "group", parent="primary-region", icon="vpc_group", stroke=C["dr"], fill="#FFFFFF", font_size=28, z=3)
    add_box("dr-vpc", "DR VPC · 10.10.0.0/16", 2120, 850, 1690, 730, "group", parent="dr-region", icon="vpc_group", stroke=C["dr"], fill="#FFFFFF", dashed=True, font_size=28, z=3)
    add_box("p-igw", "Internet Gateway", 910, 865, 250, 72, "free-resource", parent="p-vpc", icon="igw", stroke=C["dr"], font_size=19, z=25)
    add_box("dr-igw", "Internet Gateway", 2840, 865, 250, 72, "free-resource", parent="dr-vpc", icon="igw", stroke=C["dr"], dashed=True, font_size=19, z=25)

    for region, offset, az1, az2, cidr, parent in [
        ("p", 0, "2a", "2c", "10.0", "p-vpc"),
        ("dr", 1930, "1a", "1c", "10.10", "dr-vpc"),
    ]:
        stroke = C["line"] if region == "p" else C["dr"]
        add_box(f"{region}-az-a", f"AZ · {az1}", 230 + offset, 940, 760, 450, "az", parent=parent, stroke=stroke, fill="#FFFFFF", dashed=True, font_size=23, z=4)
        add_box(f"{region}-az-c", f"AZ · {az2}", 1050 + offset, 940, 760, 450, "az", parent=parent, stroke=stroke, fill="#FFFFFF", dashed=True, font_size=23, z=4)
        for suffix, x, az_parent, public, private, data in [
            ("a", 250 + offset, f"{region}-az-a", f"{cidr}.0.0/24", f"{cidr}.10.0/24", f"{cidr}.20.0/24"),
            ("c", 1070 + offset, f"{region}-az-c", f"{cidr}.1.0/24", f"{cidr}.11.0/24", f"{cidr}.21.0/24"),
        ]:
            add_box(f"{region}-public-{suffix}", f"Public · {public}", x, 985, 720, 88, "subnet", parent=az_parent, icon="public_group", stroke=C["opt"], fill=C["public_fill"], font_size=19, z=5)
            add_box(f"{region}-private-{suffix}", f"Private · {private}", x, 1083, 720, 175, "subnet", parent=az_parent, icon="private_group", stroke=C["network"], fill=C["private_fill"], font_size=19, z=5)
            add_box(f"{region}-data-{suffix}", f"Database · {data}", x, 1268, 720, 98, "subnet", parent=az_parent, icon="private_group", stroke=C["dr"], fill=C["data_fill"], font_size=19, z=5)

    # Public entry components float on top of subnet backgrounds.
    add_box("p-bastion", "Bastion\nSSM + SSH", 305, 970, 200, 105, "free-resource", parent="p-az-a", icon="ec2", stroke=C["daily"], font_size=20, z=25)
    add_box("p-nat", "NAT Gateway\nsingle", 545, 970, 200, 105, "free-resource", parent="p-az-a", icon="nat", stroke=C["daily"], font_size=19, z=25)
    add_box("p-alb", "ALB\n2 public subnets", 890, 955, 260, 125, "free-small", parent="p-vpc", icon="alb", stroke=C["daily"], font_size=22, z=25)
    add_box("p-flow", "VPC REJECT Flow Logs", 1470, 995, 300, 58, "micro", parent="p-vpc", stroke=C["obs"], fill=C["obs_fill"], font_size=18, z=25)

    add_box("dr-bastion", "Bastion\nSSM + SSH", 2235, 970, 200, 105, "free-resource", parent="dr-az-a", icon="ec2", stroke=C["dr"], dashed=True, badge="DR", font_size=20, z=25)
    add_box("dr-nat", "NAT Gateway\nsingle", 2475, 970, 200, 105, "free-resource", parent="dr-az-a", icon="nat", stroke=C["dr"], dashed=True, font_size=19, z=25)
    add_box("dr-alb", "ALB\n2 public subnets", 2820, 955, 260, 125, "free-small", parent="dr-vpc", icon="alb", stroke=C["dr"], dashed=True, badge="DR", font_size=22, z=25)

    # EKS is one visually dominant set; its internals are concise micro labels, not a card matrix.
    add_box("p-eks-box", "Amazon EKS · Private API · System + Workload", 500, 1085, 1120, 185, "eks-group", parent="p-vpc", icon="eks", stroke=C["daily"], fill="#FFFDFC", font_size=23, z=10)
    add_box("dr-eks-box", "Amazon EKS · Private API · DR profile", 2430, 1085, 1120, 185, "eks-group", parent="dr-vpc", icon="eks", stroke=C["dr"], fill=C["dr_fill"], dashed=True, badge="DR", font_size=23, z=10)

    add_box("p-eks-api", "EKS\nControl Plane", 525, 1120, 175, 135, "free-small", parent="p-eks-box", icon="eks", stroke=C["daily"], font_size=21, z=25)
    add_box("p-system-node", "System Node", 730, 1120, 250, 52, "tag", parent="p-eks-box", stroke=C["daily"], font_size=20, z=25)
    add_box("p-karpenter", "Karpenter Nodes", 995, 1120, 285, 52, "tag", parent="p-eks-box", stroke=C["daily"], font_size=20, z=25)
    add_box("p-addons", "LBC · DNS · Fluent Bit", 1295, 1120, 300, 52, "tag", parent="p-eks-box", stroke=C["operations"], font_size=19, z=25)
    add_box("p-pod-identity", "Pod Identity", 730, 1190, 250, 52, "tag", parent="p-eks-box", stroke=C["foundation"], font_size=20, z=25)
    add_box("p-argo", "Argo CD · Auto Sync", 995, 1190, 285, 52, "tag", parent="p-eks-box", stroke=C["deploy"], font_size=20, z=25)
    add_box("p-dvwa", "BANK DVWA · Pod", 1295, 1190, 300, 52, "tag", parent="p-eks-box", stroke=C["request"], font_size=20, z=25)

    add_box("dr-eks-api", "EKS\nControl Plane", 2455, 1120, 175, 135, "free-small", parent="dr-eks-box", icon="eks", stroke=C["dr"], dashed=True, font_size=21, z=25)
    add_box("dr-system-node", "System Node", 2660, 1120, 250, 52, "tag", parent="dr-eks-box", stroke=C["dr"], font_size=20, z=25)
    add_box("dr-karpenter", "Karpenter Nodes", 2925, 1120, 285, 52, "tag", parent="dr-eks-box", stroke=C["dr"], font_size=20, z=25)
    add_box("dr-addons", "LBC · DNS · Fluent Bit", 3225, 1120, 300, 52, "tag", parent="dr-eks-box", stroke=C["dr"], font_size=19, z=25)
    add_box("dr-pod-identity", "Pod Identity", 2660, 1190, 250, 52, "tag", parent="dr-eks-box", stroke=C["dr"], font_size=20, z=25)
    add_box("dr-argo", "Argo CD · OPT-IN", 2925, 1190, 285, 52, "tag", parent="dr-eks-box", stroke=C["opt"], badge="OPT", font_size=20, z=25)
    add_box("dr-dvwa", "DVWA · bootstrap", 3225, 1190, 300, 52, "tag", parent="dr-eks-box", stroke=C["dr"], font_size=20, z=25)

    # Mirrored data rows leave the center gutter free for replication arrows.
    add_box("p-efs", "EFS\n2 mount targets", 300, 1410, 240, 145, "free-small", parent="p-vpc", icon="efs", stroke=C["opt"], dashed=True, badge="OPT", font_size=22, z=25)
    add_box("p-valkey", "Valkey\nIndependent · OPT", 900, 1410, 250, 145, "free-small", parent="p-vpc", icon="valkey", stroke=C["opt"], dashed=True, badge="OPT", font_size=21, z=25)
    add_box("p-rds", "RDS MariaDB\nS-AZ / M-AZ", 1580, 1410, 240, 145, "free-small", parent="p-vpc", icon="rds", stroke=C["daily"], font_size=22, z=25)

    add_box("dr-rds", "RDS Replica\nCross-Region", 2130, 1410, 240, 145, "free-small", parent="dr-vpc", icon="rds", stroke=C["dr"], dashed=True, badge="DR", font_size=22, z=25)
    add_box("dr-valkey", "Valkey\nIndependent · OPT", 2760, 1410, 250, 145, "free-small", parent="dr-vpc", icon="valkey", stroke=C["opt"], dashed=True, badge="OPT", font_size=21, z=25)
    add_box("dr-efs", "EFS\nIndependent · OPT", 3360, 1410, 240, 145, "free-small", parent="dr-vpc", icon="efs", stroke=C["opt"], dashed=True, badge="OPT", font_size=21, z=25)

    # Bottom operations shelf: three open rails instead of nested card sections.
    add_box("observability", "Observability · Detection · Query", 150, 1680, 3700, 360, "group", parent="aws-cloud", stroke=C["obs"], fill=C["obs_fill"], font_size=30, z=2)
    add_box("audit-area", "Audit & Storage", 190, 1730, 930, 270, "rail", parent="observability", stroke=C["foundation"], fill=C["obs_fill"], font_size=23, z=3)
    add_box("detect-area", "Detection & Alert", 1160, 1730, 1230, 270, "rail", parent="observability", stroke=C["obs"], fill=C["obs_fill"], font_size=23, z=3)
    add_box("query-area", "Query & Review", 2430, 1730, 1380, 270, "rail", parent="observability", stroke=C["operations"], fill=C["obs_fill"], font_size=23, z=3)

    add_box("cloudtrail", "CloudTrail", 230, 1795, 220, 150, "free-small", parent="audit-area", icon="cloudtrail", stroke=C["foundation"], font_size=22, z=25)
    add_box("cloudwatch", "CloudWatch Logs", 510, 1795, 240, 150, "free-small", parent="audit-area", icon="cloudwatch", stroke=C["foundation"], font_size=21, z=25)
    add_box("security-s3", "Security Log S3\n30 days", 810, 1795, 240, 150, "free-small", parent="audit-area", icon="s3", stroke=C["foundation"], font_size=21, z=25)

    add_box("guardduty", "GuardDuty\nPrimary", 1200, 1795, 220, 150, "free-small", parent="detect-area", icon="guardduty", stroke=C["obs"], font_size=21, z=25)
    add_box("eventbridge", "EventBridge", 1480, 1795, 220, 150, "free-small", parent="detect-area", icon="eventbridge", stroke=C["obs"], font_size=21, z=25)
    add_box("alarm", "Metric Filter\n+ Alarm", 1760, 1820, 220, 100, "micro", parent="detect-area", stroke=C["obs"], fill="#FFFFFF", font_size=19, z=25)
    add_box("sns", "Amazon SNS", 2040, 1795, 220, 150, "free-small", parent="detect-area", icon="sns", stroke=C["obs"], font_size=21, z=25)

    add_box("logs-insights", "CloudWatch\nLogs Insights", 2470, 1820, 270, 100, "micro", parent="query-area", stroke=C["operations"], fill="#FFFFFF", font_size=19, z=25)
    add_box("athena", "Athena + Glue", 2800, 1795, 230, 150, "free-small", parent="query-area", icon="athena", stroke=C["operations"], font_size=21, z=25)
    add_box("security-review", "Security Window\nReview", 3090, 1820, 330, 100, "micro", parent="query-area", stroke=C["operations"], fill="#FFFFFF", font_size=19, z=25)

    # Local tools remain outside the AWS Cloud boundary.
    add_box("local-tools", "AWS 외부 · Local Response & Evidence", 650, 2110, 2700, 165, "group", stroke=C["line"], fill="#FFFFFF", dashed=True, font_size=25, z=2)
    add_box("grafana", "Local Grafana\nAthena / S3", 820, 2145, 430, 110, "external", icon="server", parent="local-tools", stroke=C["operations"], font_size=21, z=25)
    add_box("waf-viewer", "WAF Live Viewer\nCloudWatch Live Tail", 1390, 2145, 450, 110, "external", icon="toolkit", parent="local-tools", stroke=C["obs"], font_size=20, z=25)
    add_box("evidence", "Evidence Bundle\nSanitized · SHA-256", 1980, 2145, 450, 110, "external", icon="source", parent="local-tools", stroke=C["foundation"], font_size=20, z=25)
    add_box("runtime-note", "Source topology\nRuntime state is verified separately", 2570, 2145, 590, 110, "micro", parent="local-tools", stroke=C["line"], fill=base.C["bg"], font_size=20, z=25)


SUMMARY_ROUTES: dict[str, dict[str, object]] = {
    "req-1": {"layer": "layer-summary", "exit": (0.5, 1.0), "entry": (0.5, 0.0), "points": [(1365, 310), (1325, 310), (1325, 390)]},
    "req-2": {"layer": "layer-summary", "exit": (1.0, 0.5), "entry": (0.0, 0.5), "points": []},
    "req-3": {"layer": "layer-summary", "exit": (0.5, 1.0), "entry": (0.5, 1.0), "points": [(1840, 590), (1590, 590)]},
    "req-4": {"layer": "layer-summary", "exit": (0.5, 0.0), "entry": (0.5, 0.0), "points": [(2085, 385), (1590, 385)]},
    "req-5": {"layer": "layer-summary", "exit": (0.5, 1.0), "entry": (0.5, 0.0), "points": [(1590, 625), (1020, 625), (1020, 930)]},
    "req-6": {"layer": "layer-summary", "exit": (0.5, 1.0), "entry": (0.5, 0.0), "points": [(1020, 1080), (1445, 1080), (1445, 1175)]},
    "req-7": {"layer": "layer-summary", "exit": (0.5, 1.0), "entry": (0.5, 0.0), "points": [(1445, 1375), (1700, 1375)]},
    "dr-1": {"layer": "layer-summary", "exit": (1.0, 0.5), "entry": (0.0, 0.5), "points": []},
    "dr-2": {"layer": "layer-summary", "exit": (1.0, 0.5), "entry": (0.0, 0.5), "points": []},
    "dr-3": {"layer": "layer-summary", "exit": (0.5, 1.0), "entry": (0.5, 0.0), "points": [(2950, 1080), (3375, 1080), (3375, 1175)]},
    "obs-10": {"layer": "layer-summary", "exit": (1.0, 0.5), "entry": (0.0, 0.5), "points": []},
    "obs-12": {"layer": "layer-summary", "exit": (1.0, 0.5), "entry": (0.0, 0.5), "points": [(1700, 1780), (2150, 1780)]},
}


def build_edges_from_v9() -> None:
    base.build_edges()
    for item in base.EDGES:
        item.points = []
        if item.edge_id in SUMMARY_ROUTES:
            route = SUMMARY_ROUTES[item.edge_id]
            item.layer = str(route["layer"])
            item.exit_xy = tuple(route["exit"])  # type: ignore[arg-type]
            item.entry_xy = tuple(route["entry"])  # type: ignore[arg-type]
            item.points = list(route["points"])  # type: ignore[arg-type]
            if item.edge_id.startswith("obs-"):
                item.color = base.C["telemetry"]
                item.width = 4
            elif item.edge_id.startswith("dr-"):
                item.color = base.C["replication"] if item.edge_id in {"dr-1", "dr-2"} else base.C["dr"]
            else:
                item.color = base.C["request"]
        elif item.layer == "layer-observability":
            item.layer = "layer-observability-detail"
        elif item.layer == "layer-dr":
            item.layer = "layer-dr-detail"
        elif item.layer == "layer-request":
            item.layer = "layer-request-detail"


def icon_size(item: base.Box) -> int:
    return {
        "free-service": 104,
        "free-small": 82,
        "free-resource": 54,
        "external": 58,
    }.get(item.kind, 0)


def render_box_v11(canvas: Image.Image, item: base.Box) -> None:
    draw = ImageDraw.Draw(canvas)
    xy = (item.x, item.y, item.x + item.w, item.y + item.h)
    if item.kind == "bar":
        draw.rectangle(xy, fill=item.fill)
        return
    if item.kind in {"text", "text-muted"}:
        draw.multiline_text((item.x, item.y), item.label, font=base.font(item.font_size, item.kind == "text"), fill=base.C["ink"] if item.kind == "text" else base.C["muted"], spacing=3)
        return

    if item.kind == "rail":
        draw.text((item.x + 8, item.y + 5), item.label, font=base.font(item.font_size, True), fill=item.stroke)
        draw.line((item.x, item.y + 38, item.x + item.w, item.y + 38), fill=item.stroke, width=3)
        return

    if item.kind == "tag":
        draw.rounded_rectangle((item.x + 5, item.y + 8, item.x + 11, item.y + item.h - 8), radius=3, fill=item.stroke)
        draw.text((item.x + 22, item.y + 13), item.label, font=base.font(item.font_size, True), fill=base.C["ink"])
        if item.badge:
            badge_w = max(58, len(item.badge) * 13 + 20)
            bx = item.x + item.w - badge_w - 5
            by = item.y + 11
            draw.rounded_rectangle((bx, by, bx + badge_w, by + 28), radius=14, fill=item.stroke)
            base.centered_text(draw, (bx, by, bx + badge_w, by + 28), item.badge, 13, color="#FFFFFF")
        return

    if item.kind in {"free-service", "free-small", "free-resource"}:
        if item.dashed:
            base.draw_dashed_rectangle(draw, xy, "#FFFFFF", item.stroke, width=2, dash=10, gap=8, radius=10)
        size = icon_size(item)
        if item.icon:
            base.paste_icon(canvas, item.icon, item.x + (item.w - size) // 2, item.y + 4, size)
        base.centered_text(draw, (item.x + 2, item.y + size + 10, item.x + item.w - 2, item.y + item.h - 2), item.label, item.font_size, bold=True, spacing=2)
    else:
        radius = 14 if item.kind in {"external", "micro", "legend"} else 4
        if item.dashed:
            base.draw_dashed_rectangle(draw, xy, item.fill, item.stroke, width=3, radius=radius)
        else:
            width = 4 if item.kind in {"group", "eks-group"} else 2
            draw.rounded_rectangle(xy, radius=radius, fill=item.fill, outline=item.stroke, width=width)

        if item.kind in {"group", "az", "subnet", "eks-group"}:
            title_x = item.x + 15
            if item.icon:
                size = 38 if item.kind in {"group", "eks-group"} else 28
                base.paste_icon(canvas, item.icon, item.x + 10, item.y + 8, size)
                title_x = item.x + size + 18
            draw.text((title_x, item.y + 9), item.label, font=base.font(item.font_size, True), fill=item.stroke if item.kind in {"group", "eks-group"} else base.C["ink"])
        elif item.kind == "external":
            size = icon_size(item)
            if item.icon:
                base.paste_icon(canvas, item.icon, item.x + 10, item.y + (item.h - size) // 2, size)
            base.centered_text(draw, (item.x + size + 18, item.y + 5, item.x + item.w - 5, item.y + item.h - 5), item.label, item.font_size, bold=True, spacing=2)
        else:
            base.centered_text(draw, xy, item.label, item.font_size, bold=True, spacing=3)

    if item.badge:
        badge_w = max(58, len(item.badge) * 13 + 20)
        bx = item.x + item.w - badge_w - 5
        by = item.y + 5
        draw.rounded_rectangle((bx, by, bx + badge_w, by + 28), radius=14, fill=item.stroke)
        base.centered_text(draw, (bx, by, bx + badge_w, by + 28), item.badge, 13, color="#FFFFFF")


def image_style_free(item: base.Box) -> str:
    size = icon_size(item)
    data = base64.b64encode(base.ICON_PATHS[item.icon or "user"].read_bytes()).decode("ascii")
    stroke = item.stroke if item.dashed else "none"
    fill = "#FFFFFF" if item.dashed else "none"
    style = (
        "shape=label;rounded=0;whiteSpace=wrap;html=1;"
        f"image=data:image/png,{data};imageWidth={size};imageHeight={size};"
        "imageAlign=center;imageVerticalAlign=top;align=center;verticalAlign=bottom;"
        "spacingTop=4;spacingBottom=2;spacingLeft=2;spacingRight=2;"
        f"fillColor={fill};strokeColor={stroke};strokeWidth=2;"
        f"fontFamily=Malgun Gothic;fontSize={item.font_size};fontStyle=1;shadow=0;"
    )
    if item.dashed:
        style += "dashed=1;dashPattern=10 8;"
    return style


def box_style_v11(item: base.Box) -> str:
    if item.kind in {"free-service", "free-small", "free-resource"}:
        return image_style_free(item)
    if item.kind == "external" and item.icon:
        data = base64.b64encode(base.ICON_PATHS[item.icon].read_bytes()).decode("ascii")
        return (
            "shape=label;rounded=1;arcSize=12;whiteSpace=wrap;html=1;"
            f"image=data:image/png,{data};imageWidth=58;imageHeight=58;imageAlign=left;imageVerticalAlign=middle;"
            "align=center;verticalAlign=middle;spacingLeft=70;"
            f"fillColor={item.fill};strokeColor={item.stroke};strokeWidth=2;"
            f"fontFamily=Malgun Gothic;fontSize={item.font_size};fontStyle=1;shadow=0;"
        )
    if item.kind == "rail":
        return (
            "shape=line;html=1;align=left;verticalAlign=top;labelPosition=left;verticalLabelPosition=top;"
            f"strokeColor={item.stroke};strokeWidth=3;fillColor=none;fontColor={item.stroke};"
            f"fontFamily=Malgun Gothic;fontSize={item.font_size};fontStyle=1;spacingTop=4;"
        )
    if item.kind == "tag":
        return (
            "text;html=1;align=left;verticalAlign=middle;spacingLeft=12;whiteSpace=wrap;"
            f"fontFamily=Malgun Gothic;fontSize={item.font_size};fontStyle=1;fontColor={base.C['ink']};"
            "strokeColor=none;fillColor=none;shadow=0;"
        )
    if item.kind in {"group", "az", "subnet", "eks-group"}:
        style = (
            "shape=label;container=1;collapsible=0;recursiveResize=0;rounded=0;whiteSpace=wrap;html=1;"
            "align=left;verticalAlign=top;spacingTop=9;spacingLeft=56;spacingRight=6;"
            f"fillColor={item.fill};strokeColor={item.stroke};strokeWidth=3;"
            f"fontFamily=Malgun Gothic;fontSize={item.font_size};fontStyle=1;shadow=0;"
        )
        if item.icon:
            data = base64.b64encode(base.ICON_PATHS[item.icon].read_bytes()).decode("ascii")
            size = 38 if item.kind in {"group", "eks-group"} else 28
            style += f"image=data:image/png,{data};imageWidth={size};imageHeight={size};imageAlign=left;imageVerticalAlign=top;"
        if item.dashed:
            style += "dashed=1;dashPattern=10 8;"
        return style
    if item.kind == "bar":
        return f"rounded=0;fillColor={item.fill};strokeColor={item.stroke};"
    if item.kind in {"text", "text-muted"}:
        color = base.C["ink"] if item.kind == "text" else base.C["muted"]
        bold = 1 if item.kind == "text" else 0
        return f"text;html=1;align=left;verticalAlign=middle;fontFamily=Malgun Gothic;fontSize={item.font_size};fontStyle={bold};fontColor={color};strokeColor=none;fillColor=none;"
    style = (
        "rounded=1;arcSize=12;whiteSpace=wrap;html=1;align=center;verticalAlign=middle;"
        f"fillColor={item.fill};strokeColor={item.stroke};strokeWidth=2;"
        f"fontFamily=Malgun Gothic;fontSize={item.font_size};fontStyle=1;shadow=0;"
    )
    if item.dashed:
        style += "dashed=1;dashPattern=10 8;"
    return style


def html_value_v11(item: base.Box) -> str:
    lines = item.label.split("\n")
    if item.kind in {"free-service", "free-small", "free-resource", "external"} and len(lines) > 1:
        title = html.escape(lines[0])
        subtitle = html.escape(" · ".join(lines[1:]))
        return f'<div style="text-align:center;line-height:1.12;"><b>{title}</b><br><span style="font-size:{max(16, item.font_size - 4)}px;color:{base.C["muted"]};font-weight:400;">{subtitle}</span></div>'
    return "<br>".join(html.escape(line) for line in lines)


def add_edge_v11(root: ET.Element, item: base.Edge) -> None:
    style = (
        "edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;"
        f"strokeWidth={item.width};strokeColor={item.color};endArrow=block;endFill=1;"
        f"fontFamily=Malgun Gothic;fontSize=19;fontStyle=1;labelBackgroundColor={base.C['white']};"
        f"exitX={item.exit_xy[0]};exitY={item.exit_xy[1]};entryX={item.entry_xy[0]};entryY={item.entry_xy[1]};"
        "exitDx=0;exitDy=0;entryDx=0;entryDy=0;"
    )
    if item.dashed:
        style += "dashed=1;dashPattern=10 8;"
    cell = ET.SubElement(root, "mxCell", {"id": item.edge_id, "value": item.label, "style": style, "edge": "1", "parent": item.layer, "source": item.source, "target": item.target, "dataFlow": item.layer.replace("layer-", "")})
    geometry = ET.SubElement(cell, "mxGeometry", {"relative": "1", "as": "geometry"})
    if item.points:
        arr = ET.SubElement(geometry, "Array", {"as": "points"})
        for x, y in item.points:
            ET.SubElement(arr, "mxPoint", {"x": str(x), "y": str(y)})


def write_drawio_v11(path: Path) -> None:
    mxfile = ET.Element("mxfile", {"host": "app.diagrams.net", "modified": "2026-08-11T00:00:00.000Z", "agent": "Codex", "version": "24.7.17", "type": "device", "compressed": "false"})
    diagram = ET.SubElement(mxfile, "diagram", {"name": "11 · MENTOR OVERVIEW · REFERENCE LAYOUT", "id": "mentor-reference-v11"})
    model = ET.SubElement(diagram, "mxGraphModel", {"dx": "1600", "dy": "900", "grid": "1", "gridSize": "10", "guides": "1", "tooltips": "1", "connect": "1", "arrows": "1", "fold": "1", "page": "1", "pageScale": "1", "pageWidth": str(PAGE_W), "pageHeight": str(PAGE_H), "math": "0", "shadow": "0"})
    root = ET.SubElement(model, "root")
    ET.SubElement(root, "mxCell", {"id": "0"})
    layers = [
        ("layer-summary", "01 · Summary Flow", True),
        ("layer-deployment", "02 · Deployment Detail", False),
        ("layer-operations", "03 · Operations Detail", False),
        ("layer-request-detail", "04 · Request Detail", False),
        ("layer-dr-detail", "05 · DR Detail", False),
        ("layer-observability-detail", "06 · Observability Detail", False),
        ("layer-topology", "00 · Full Topology", True),
    ]
    for layer_id, label, visible in layers:
        attrs = {"id": layer_id, "value": label, "parent": "0"}
        if not visible:
            attrs["visible"] = "0"
        ET.SubElement(root, "mxCell", attrs)

    by_id = {item.box_id: item for item in base.BOXES}
    for item in base.EDGES:
        add_edge_v11(root, item)
    for item in base.BOXES:
        base.add_vertex(root, item, by_id)
        base.add_badge_vertex(root, item, by_id)

    ET.indent(mxfile, space="  ")
    path.write_text('<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(mxfile, encoding="unicode"), encoding="utf-8", newline="\n")


def render_preview_v11(path: Path) -> None:
    canvas = Image.new("RGBA", (PAGE_W, PAGE_H), base.rgb(base.C["bg"]) + (255,))
    by_id = {item.box_id: item for item in base.BOXES}
    ordered = sorted(base.BOXES, key=lambda value: value.z)
    for item in (value for value in ordered if value.z <= 10):
        render_box_v11(canvas, item)

    draw = ImageDraw.Draw(canvas)
    for item in base.EDGES:
        if item.layer != "layer-summary":
            continue
        points = base.edge_points(item, by_id)
        if item.dashed:
            base.dashed_polyline(draw, points, item.color, item.width)
        else:
            draw.line(points, fill=item.color, width=item.width, joint="curve")
        base.arrowhead(draw, points[-2], points[-1], item.color, max(15, item.width * 4))
        if item.label:
            mid = points[len(points) // 2]
            f = base.font(18, True)
            bounds = draw.textbbox((0, 0), item.label, font=f)
            tw = bounds[2] - bounds[0]
            th = bounds[3] - bounds[1]
            draw.rounded_rectangle((mid[0] - tw / 2 - 7, mid[1] - th / 2 - 5, mid[0] + tw / 2 + 7, mid[1] + th / 2 + 5), radius=5, fill="#FFFFFF")
            draw.text((mid[0] - tw / 2, mid[1] - th / 2), item.label, font=f, fill=item.color)

    for item in (value for value in ordered if value.z > 10):
        render_box_v11(canvas, item)
    path.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(path, quality=96)


def validate_model(source_box_ids: set[str], source_edge_ids: set[str]) -> None:
    actual_box_ids = {item.box_id for item in base.BOXES}
    actual_edge_ids = {item.edge_id for item in base.EDGES}
    if actual_box_ids != source_box_ids:
        raise ValueError(f"v9 box coverage mismatch: missing={sorted(source_box_ids - actual_box_ids)} extra={sorted(actual_box_ids - source_box_ids)}")
    if actual_edge_ids != source_edge_ids:
        raise ValueError(f"v9 edge coverage mismatch: missing={sorted(source_edge_ids - actual_edge_ids)} extra={sorted(actual_edge_ids - source_edge_ids)}")
    by_id = {item.box_id: item for item in base.BOXES}
    for item in base.BOXES:
        if item.x < 0 or item.y < 0 or item.x + item.w > PAGE_W or item.y + item.h > PAGE_H:
            raise ValueError(f"out-of-page box: {item.box_id}")
        if item.parent in by_id:
            parent = by_id[item.parent]
            if not (parent.x <= item.x and parent.y <= item.y and item.x + item.w <= parent.x + parent.w and item.y + item.h <= parent.y + parent.h):
                raise ValueError(f"child outside parent: {item.box_id} -> {item.parent}")
    for item in base.EDGES:
        if item.source not in by_id or item.target not in by_id:
            raise ValueError(f"missing edge endpoint: {item.edge_id}")
        for x, y in item.points:
            if not (0 <= x <= PAGE_W and 0 <= y <= PAGE_H):
                raise ValueError(f"out-of-page edge waypoint: {item.edge_id} ({x}, {y})")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--drawio", type=Path, default=HERE / "11_MENTOR_OVERVIEW__REFERENCE_LAYOUT__v11.drawio")
    parser.add_argument("--preview", type=Path)
    args = parser.parse_args()

    base.BOXES.clear()
    base.EDGES.clear()
    base.build_boxes()
    base.build_edges()
    source_box_ids = {item.box_id for item in base.BOXES}
    source_edge_ids = {item.edge_id for item in base.EDGES}

    base.PAGE_W = PAGE_W
    base.PAGE_H = PAGE_H
    base.BOXES.clear()
    base.EDGES.clear()
    base.box_style = box_style_v11
    base.html_value = html_value_v11

    base.verify_assets()
    build_boxes()
    build_edges_from_v9()
    validate_model(source_box_ids, source_edge_ids)
    write_drawio_v11(args.drawio)
    if args.preview:
        render_preview_v11(args.preview)
    print(args.drawio)
    if args.preview:
        print(args.preview)


if __name__ == "__main__":
    main()
