from __future__ import annotations

import argparse
import base64
import html
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image, ImageDraw

import generate_mentor_full_topology_v9 as base


HERE = Path(__file__).resolve().parent
PAGE_W = 4000
PAGE_H = 2400


def box(
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
    font_size: int = 28,
    z: int = 20,
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
            font_size=font_size,
            z=z,
        )
    )


def build_boxes() -> None:
    C = base.C

    # Header and the AWS Cloud boundary.
    box("header-accent", "", 0, 0, PAGE_W, 12, "bar", fill="#FF9900", stroke="#FF9900", z=0)
    box(
        "header-title",
        "멘토용 전체 인프라\nAWS Cloud → Region → VPC → AZ → Subnet · Terraform Source 기준",
        34,
        18,
        3900,
        100,
        "text",
        font_size=42,
        z=40,
    )
    box("aws-cloud", "AWS Cloud", 300, 130, 3660, 1990, "group", icon="cloud_group", stroke=C["ink"], fill="#FBFCFD", font_size=34, z=1)

    # Shared services and lifecycle summary.
    box("edge-zone", "Global Edge · DNS · Identity", 340, 180, 1760, 340, "group", parent="aws-cloud", stroke=C["foundation"], fill=C["foundation_fill"], font_size=32, z=2)
    box(
        "lifecycle-note",
        "Runtime Profiles\nminimal (LAB · cost)  Primary / EKS 1 / RDS Single-AZ\ndr-test  + DR\nfull  + DR / EKS 2 / RDS Multi-AZ\nOPT-IN  Valkey / EFS / S3 access",
        2160,
        180,
        1760,
        340,
        "note",
        parent="aws-cloud",
        stroke=C["line"],
        fill="#FFFFFF",
        font_size=32,
        z=2,
    )

    shared = [
        ("route53", "Route 53\nDNS", 375, "route53", C["foundation"]),
        ("cloudfront", "CloudFront\nPrimary origin", 650, "cloudfront", C["foundation"]),
        ("acm", "ACM\nTLS", 925, "acm", C["obs"]),
        ("waf", "AWS WAF\nCOUNT", 1200, "waf", C["obs"]),
        ("iam", "AWS IAM\nOIDC · Roles", 1475, "iam", C["foundation"]),
        ("ssm", "Systems Manager\nAdd-ons", 1750, "ssm", C["operations"]),
    ]
    for node_id, label, x, icon, stroke in shared:
        box(node_id, label, x, 245, 250, 230, "service", parent="edge-zone", icon=icon, stroke=stroke, fill="#FFFFFF", font_size=26, z=25)

    # Equal-weight Primary and DR regions.
    box("primary-region", "Primary · Seoul  |  ap-northeast-2", 340, 560, 1760, 1080, "group", parent="aws-cloud", icon="region_group", stroke=C["network"], fill="#F9FDFD", font_size=34, z=2)
    box("dr-region", "DR · Tokyo  |  ap-northeast-1", 2160, 560, 1760, 1080, "group", parent="aws-cloud", icon="region_group", stroke=C["dr"], fill=C["dr_fill"], dashed=True, font_size=34, z=2)

    box("primary-regional-services", "Regional Services", 380, 630, 1680, 185, "subgroup", parent="primary-region", stroke=C["line"], fill="#FFFFFF", font_size=28, z=3)
    box("dr-regional-services", "Regional Services", 2200, 630, 1680, 185, "subgroup", parent="dr-region", stroke=C["dr"], fill="#FFFFFF", dashed=True, font_size=28, z=3)
    box("ecr", "Amazon ECR\nImages", 610, 640, 250, 165, "service-small", parent="primary-regional-services", icon="ecr", stroke=C["daily"], font_size=26, z=25)
    box("p-s3", "Application S3\nAccess · OPT-IN", 1010, 640, 270, 165, "service-small", parent="primary-regional-services", icon="s3", stroke=C["opt"], dashed=True, font_size=24, z=25)
    box("dr-s3", "Application S3\nPROFILE", 2350, 640, 270, 165, "service-small", parent="dr-regional-services", icon="s3", stroke=C["dr"], dashed=True, font_size=25, z=25)
    box("dr-note", "DR profile only\nNo automatic failover · No application bootstrap", 2780, 650, 1000, 145, "note", parent="dr-regional-services", stroke=C["dr"], fill="#FFFFFF", dashed=True, font_size=24, z=25)

    # VPC, AZ and subnet hierarchy.
    box("primary-vpc", "Primary VPC · 10.0.0.0/16", 380, 830, 1680, 790, "group", parent="primary-region", icon="vpc_group", stroke=C["dr"], fill="#FFFFFF", font_size=31, z=3)
    box("dr-vpc", "DR VPC · 10.10.0.0/16", 2200, 830, 1680, 790, "group", parent="dr-region", icon="vpc_group", stroke=C["dr"], fill="#FFFFFF", dashed=True, font_size=31, z=3)

    box("p-az-a", "AZ · 2a", 420, 900, 560, 470, "az", parent="primary-vpc", stroke=C["line"], fill="#FFFFFF", dashed=True, font_size=27, z=4)
    box("p-multi-az-lane", "Managed Services", 1000, 900, 440, 470, "az", parent="primary-vpc", stroke=C["dr"], fill="#FAF7FF", dashed=True, font_size=27, z=4)
    box("p-az-c", "AZ · 2c", 1460, 900, 560, 470, "az", parent="primary-vpc", stroke=C["line"], fill="#FFFFFF", dashed=True, font_size=27, z=4)

    box("dr-az-a", "AZ · 1a", 2240, 900, 560, 470, "az", parent="dr-vpc", stroke=C["line"], fill="#FFFFFF", dashed=True, font_size=27, z=4)
    box("dr-multi-az-lane", "Managed Services", 2820, 900, 440, 470, "az", parent="dr-vpc", stroke=C["dr"], fill="#FAF7FF", dashed=True, font_size=27, z=4)
    box("dr-az-c", "AZ · 1c", 3280, 900, 560, 470, "az", parent="dr-vpc", stroke=C["line"], fill="#FFFFFF", dashed=True, font_size=27, z=4)

    subnet_specs = [
        ("p-2a", 440, "10.0.0.0/24", "10.0.10.0/24", "10.0.20.0/24", "p-az-a"),
        ("p-2c", 1480, "10.0.1.0/24", "10.0.11.0/24", "10.0.21.0/24", "p-az-c"),
        ("dr-1a", 2260, "10.10.0.0/24", "10.10.10.0/24", "10.10.20.0/24", "dr-az-a"),
        ("dr-1c", 3300, "10.10.1.0/24", "10.10.11.0/24", "10.10.21.0/24", "dr-az-c"),
    ]
    for prefix, x, public_cidr, private_cidr, data_cidr, parent in subnet_specs:
        box(f"{prefix}-public", f"Public\n{public_cidr}", x, 960, 520, 100, "subnet", parent=parent, icon="public_group", stroke=C["opt"], fill=C["public_fill"], font_size=23, z=5)
        box(f"{prefix}-private", f"Private\n{private_cidr}", x, 1070, 520, 160, "subnet", parent=parent, icon="private_group", stroke=C["network"], fill=C["private_fill"], font_size=23, z=5)
        box(f"{prefix}-database", f"Database\n{data_cidr}", x, 1240, 520, 105, "subnet", parent=parent, icon="private_group", stroke=C["dr"], fill=C["data_fill"], font_size=23, z=5)

    # Workload and operations in the Primary region.
    box("p-bastion", "Bastion\nSSM · SSH", 610, 955, 220, 105, "resource", parent="p-az-a", icon="ec2", stroke=C["daily"], font_size=23, z=25)
    box("p-alb", "ALB\nPublic", 1105, 935, 230, 170, "service-small", parent="p-multi-az-lane", icon="alb", stroke=C["daily"], font_size=28, z=25)
    box("p-eks", "EKS\nPrivate API", 1020, 1120, 190, 190, "service", parent="p-multi-az-lane", icon="eks", stroke=C["daily"], font_size=28, z=25)
    box("pod-identity", "Pod Identity\nPod roles", 1230, 1120, 190, 190, "service-small", parent="p-multi-az-lane", icon="iam", stroke=C["foundation"], font_size=25, z=25)
    box("argocd", "Argo CD · Auto Sync", 1080, 1320, 280, 45, "chip", parent="p-multi-az-lane", stroke=C["deploy"], fill="#F4FBF1", font_size=23, z=25)

    # DR workload equivalents.
    box("dr-bastion", "Bastion\nPROFILE", 2430, 955, 220, 105, "resource", parent="dr-az-a", icon="ec2", stroke=C["dr"], dashed=True, font_size=23, z=25)
    box("dr-alb", "ALB\nPROFILE", 2925, 935, 230, 170, "service-small", parent="dr-multi-az-lane", icon="alb", stroke=C["dr"], dashed=True, font_size=28, z=25)
    box("dr-eks", "EKS\nPROFILE · no app", 2945, 1130, 190, 190, "service", parent="dr-multi-az-lane", icon="eks", stroke=C["dr"], dashed=True, font_size=25, z=25)

    # Regional data services remain visually separate from AZ placement.
    box("primary-data", "Data Services", 420, 1390, 1600, 210, "subgroup", parent="primary-vpc", stroke=C["dr"], fill="#FFFFFF", dashed=True, font_size=25, z=4)
    box("dr-data", "DR Data Services · PROFILE", 2240, 1390, 1600, 210, "subgroup", parent="dr-vpc", stroke=C["dr"], fill="#FFFFFF", dashed=True, font_size=25, z=4)

    box("p-rds", "RDS\nmin S-AZ · full M-AZ", 530, 1430, 300, 160, "service-small", parent="primary-data", icon="rds", stroke=C["daily"], font_size=21, z=25)
    box("p-valkey", "Valkey\nOPT-IN", 1060, 1430, 300, 160, "service-small", parent="primary-data", icon="valkey", stroke=C["opt"], dashed=True, font_size=24, z=25)
    box("p-efs", "EFS\nOPT-IN", 1590, 1430, 300, 160, "service-small", parent="primary-data", icon="efs", stroke=C["opt"], dashed=True, font_size=24, z=25)

    box("dr-rds", "RDS\nRead replica", 2350, 1430, 300, 160, "service-small", parent="dr-data", icon="rds", stroke=C["dr"], dashed=True, font_size=23, z=25)
    box("dr-valkey", "Valkey\nPROFILE · OPT-IN", 2880, 1430, 300, 160, "service-small", parent="dr-data", icon="valkey", stroke=C["opt"], dashed=True, font_size=21, z=25)
    box("dr-efs", "EFS\nPROFILE · OPT-IN", 3410, 1430, 300, 160, "service-small", parent="dr-data", icon="efs", stroke=C["opt"], dashed=True, font_size=21, z=25)

    box("primary-sg-note", "ACTIVE · PROFILE · OPT-IN · Security Group / Target Group omitted", 340, 1645, 3580, 38, "text-muted", parent="aws-cloud", font_size=22, z=30)

    # Observability remains a single operational rail; detailed log flow stays in its own diagram.
    box("observability", "Observability · Detection · Operations", 340, 1695, 3580, 375, "group", parent="aws-cloud", stroke=C["obs"], fill=C["obs_fill"], font_size=32, z=2)
    obs_nodes = [
        ("cloudtrail", "CloudTrail\nAudit", 450, "cloudtrail"),
        ("guardduty", "GuardDuty\nPrimary", 820, "guardduty"),
        ("eventbridge", "EventBridge\nRoute", 1190, "eventbridge"),
        ("sns", "Amazon SNS\nAlert", 1560, "sns"),
        ("cloudwatch", "CloudWatch\nLogs · Metrics", 1930, "cloudwatch"),
        ("security-s3", "Security S3\nEvidence · 30d", 2300, "s3"),
    ]
    for node_id, label, x, icon in obs_nodes:
        box(node_id, label, x, 1780, 250, 205, "service", parent="observability", icon=icon, stroke=C["obs"], font_size=27, z=25)
    box("local-detail", "Source → Detect → Alert → Respond", 2710, 1810, 1040, 135, "note", parent="observability", stroke=C["operations"], fill="#FFFFFF", font_size=29, z=25)

    # External actors and local response tools stay outside AWS boundaries.
    box("actor", "User / Attacker\nHTTPS", 20, 270, 240, 145, "external", icon="user", stroke=C["line"], font_size=25, z=30)
    box("github", "GitHub CI\nBuild · Push", 20, 640, 240, 145, "external", icon="source", stroke=C["deploy"], font_size=25, z=30)
    box("git-repo", "Git Repo\nvalues.yaml", 20, 810, 240, 130, "external", icon="source", stroke=C["deploy"], font_size=24, z=30)
    box("operator-pc", "Operator\ndaily-up/down", 20, 980, 240, 145, "external", icon="toolkit", stroke=C["operations"], font_size=24, z=30)

    box("local-tools", "AWS 외부 · Local Response Tools", 1050, 2160, 1900, 220, "group", stroke=C["line"], fill="#FFFFFF", dashed=True, font_size=28, z=2)
    box("grafana", "Local Grafana\nAthena / S3", 1280, 2200, 420, 160, "external", icon="server", parent="local-tools", stroke=C["operations"], font_size=24, z=25)
    box("waf-viewer", "WAF Live Viewer\nLive Tail", 2000, 2200, 440, 160, "external", icon="toolkit", parent="local-tools", stroke=C["obs"], font_size=24, z=25)


def build_edges() -> None:
    C = base.C

    # Request path.
    base.edge("e-user-route", "actor", "route53", "layer-request", C["request"], label="HTTPS", width=5)
    base.edge("e-route-cf", "route53", "cloudfront", "layer-request", C["request"], label="DNS", width=5)
    base.edge("e-acm-cf", "acm", "cloudfront", "layer-request", C["request"], label="TLS", dashed=True, width=3, exit_xy=(0.5, 1.0), entry_xy=(0.5, 1.0), points=[(1065, 495), (785, 495)])
    base.edge("e-waf-cf", "waf", "cloudfront", "layer-request", C["request"], label="WAF", dashed=True, width=3, exit_xy=(0.5, 0.0), entry_xy=(0.5, 0.0), points=[(1345, 230), (785, 230)])
    base.edge("e-cf-alb", "cloudfront", "p-alb", "layer-request", C["request"], width=5, exit_xy=(0.5, 1.0), entry_xy=(0.5, 0.0), points=[(785, 545), (1040, 545), (1040, 815), (1220, 815)])
    base.edge("e-palb-peks", "p-alb", "p-eks", "layer-request", C["request"], label=":80", width=5, exit_xy=(0.5, 1.0), entry_xy=(0.5, 0.0))
    base.edge("e-dralb-dreks", "dr-alb", "dr-eks", "layer-request", C["dr"], label=":80", dashed=True, width=4, exit_xy=(0.5, 1.0), entry_xy=(0.5, 0.0))

    # Deployment path.
    base.edge("e-github-ecr", "github", "ecr", "layer-deployment", C["deploy"], width=4)
    base.edge("e-github-argo", "github", "git-repo", "layer-deployment", C["deploy"], label="values.yaml", width=4, exit_xy=(0.5, 1.0), entry_xy=(0.5, 0.0))
    base.edge("e-repo-argo", "git-repo", "argocd", "layer-deployment", C["deploy"], width=4, exit_xy=(1.0, 0.5), entry_xy=(0.0, 0.5), points=[(300, 875), (300, 1342), (1060, 1342)])
    base.edge("e-argo-peks", "argocd", "p-eks", "layer-deployment", C["deploy"], width=4, exit_xy=(0.25, 0.0), entry_xy=(0.5, 1.0))
    base.edge("e-ecr-peks", "ecr", "p-eks", "layer-deployment", C["deploy"], dashed=True, width=3, exit_xy=(0.5, 1.0), entry_xy=(0.0, 0.5), points=[(735, 815), (980, 815), (980, 1215)])

    # Operations and identity path.
    base.edge("e-ssm-pbastion", "ssm", "p-bastion", "layer-operations", C["operations"], dashed=True, width=3, exit_xy=(0.5, 1.0), entry_xy=(0.5, 0.0), points=[(1905, 610), (720, 610), (720, 940)])
    base.edge("e-ssm-drbastion", "ssm", "dr-bastion", "layer-operations", C["operations"], dashed=True, width=3, exit_xy=(0.5, 1.0), entry_xy=(0.5, 0.0), points=[(1905, 600), (2540, 600), (2540, 940)])
    base.edge("e-iam-pod", "iam", "pod-identity", "layer-operations", C["operations"], dashed=True, width=3, exit_xy=(0.5, 1.0), entry_xy=(1.0, 0.5), points=[(1625, 815), (1450, 815), (1450, 1215)])
    base.edge("e-operator-bastion", "operator-pc", "p-bastion", "layer-operations", C["operations"], label="SSH/SCP", width=4)
    base.edge("e-pbastion-peks", "p-bastion", "p-eks", "layer-operations", C["operations"], width=4, exit_xy=(1.0, 0.5), entry_xy=(0.0, 0.5), points=[(950, 1007), (950, 1215)])
    base.edge("e-drbastion-dreks", "dr-bastion", "dr-eks", "layer-operations", C["operations"], dashed=True, width=3, exit_xy=(1.0, 0.5), entry_xy=(0.0, 0.5), points=[(2770, 1007), (2770, 1225)])
    base.edge("e-peks-data", "p-eks", "p-rds", "layer-operations", C["operations"], width=4, exit_xy=(0.5, 1.0), entry_xy=(0.5, 0.0), points=[(1115, 1380), (680, 1380)])

    # Cross-region relationships.
    base.edge("e-rds-replication", "p-rds", "dr-rds", "layer-dr", C["replication"], label="RDS replica", dashed=True, width=5, exit_xy=(0.5, 1.0), entry_xy=(0.5, 1.0), points=[(680, 1600), (2500, 1600)])
    base.edge("e-s3-replication", "p-s3", "dr-s3", "layer-dr", C["replication"], label="S3 replica", dashed=True, width=5)

    # Detection chain.
    base.edge("e-gd-eb", "guardduty", "eventbridge", "layer-observability", C["telemetry"], width=4)
    base.edge("e-eb-sns", "eventbridge", "sns", "layer-observability", C["telemetry"], width=4)


def render_box_v10(canvas: Image.Image, item: base.Box) -> None:
    draw = ImageDraw.Draw(canvas)
    xy = (item.x, item.y, item.x + item.w, item.y + item.h)
    if item.kind == "bar":
        draw.rectangle(xy, fill=item.fill)
        return
    if item.kind in {"text", "text-muted"}:
        draw.multiline_text(
            (item.x, item.y),
            item.label,
            font=base.font(item.font_size, item.kind == "text"),
            fill=base.C["ink"] if item.kind == "text" else base.C["muted"],
            spacing=4,
        )
        return

    radius = 16 if item.kind in {"external", "note", "chip"} else 5
    if item.dashed:
        base.draw_dashed_rectangle(draw, xy, item.fill, item.stroke, width=3, radius=radius)
    else:
        width = 4 if item.kind in {"group", "eks-group"} else 2
        draw.rounded_rectangle(xy, radius=radius, fill=item.fill, outline=item.stroke, width=width)

    if item.kind in {"group", "subgroup", "az", "subnet", "eks-group"}:
        icon_size = 42 if item.kind in {"group", "eks-group"} else 30
        title_x = item.x + 16
        if item.icon:
            base.paste_icon(canvas, item.icon, item.x + 12, item.y + 8, icon_size)
            title_x = item.x + 20 + icon_size
        draw.text((title_x, item.y + 10), item.label, font=base.font(item.font_size, True), fill=item.stroke if item.kind in {"group", "eks-group"} else base.C["ink"])
    elif item.kind in {"service", "service-small", "resource", "external"}:
        icon_size = {"service": 112, "service-small": 88, "resource": 62, "external": 70}[item.kind]
        if item.icon:
            base.paste_icon(canvas, item.icon, item.x + (item.w - icon_size) // 2, item.y + 7, icon_size)
        label_top = item.y + icon_size + 13 if item.icon else item.y + 8
        base.centered_text(draw, (item.x + 4, label_top, item.x + item.w - 4, item.y + item.h - 4), item.label, item.font_size, bold=True, spacing=2)
    else:
        base.centered_text(draw, xy, item.label, item.font_size, bold=True, spacing=4)


def image_style_v10(key: str, image_w: int, image_h: int, stroke: str, fill: str, font_size: int, dashed: bool = False) -> str:
    data = base64.b64encode(base.ICON_PATHS[key].read_bytes()).decode("ascii")
    style = (
        "shape=label;rounded=0;whiteSpace=wrap;html=1;"
        f"image=data:image/png,{data};imageWidth={image_w};imageHeight={image_h};"
        "imageAlign=center;imageVerticalAlign=top;align=center;verticalAlign=bottom;"
        "spacingTop=8;spacingBottom=5;spacingLeft=4;spacingRight=4;"
        f"fillColor={fill};strokeColor={stroke};strokeWidth=1;"
        f"fontFamily=Malgun Gothic;fontSize={font_size};fontStyle=1;shadow=0;"
    )
    if dashed:
        style += "dashed=1;dashPattern=10 8;"
    return style


def group_style_v10(item: base.Box) -> str:
    style = (
        "shape=label;container=1;collapsible=0;recursiveResize=0;rounded=0;"
        "whiteSpace=wrap;html=1;align=left;verticalAlign=top;"
        "spacingTop=10;spacingLeft=62;spacingRight=8;"
        f"fillColor={item.fill};strokeColor={item.stroke};strokeWidth=3;"
        f"fontFamily=Malgun Gothic;fontSize={item.font_size};fontStyle=1;shadow=0;"
    )
    if item.icon:
        data = base64.b64encode(base.ICON_PATHS[item.icon].read_bytes()).decode("ascii")
        style += f"image=data:image/png,{data};imageWidth=42;imageHeight=42;imageAlign=left;imageVerticalAlign=top;"
    if item.dashed:
        style += "dashed=1;dashPattern=10 8;"
    return style


def box_style_v10(item: base.Box) -> str:
    if item.kind in {"group", "subgroup", "az", "subnet", "eks-group"}:
        return group_style_v10(item)
    if item.kind in {"service", "service-small", "resource", "external"} and item.icon:
        size = {"service": 112, "service-small": 88, "resource": 62, "external": 70}[item.kind]
        return image_style_v10(item.icon, size, size, item.stroke, item.fill, item.font_size, item.dashed)
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


def html_value_v10(item: base.Box) -> str:
    lines = item.label.split("\n")
    if item.kind in {"service", "service-small", "resource", "external"} and len(lines) > 1:
        title = html.escape(lines[0])
        subtitle = html.escape(" · ".join(lines[1:]))
        return f'<div style="text-align:center;line-height:1.14;"><b>{title}</b><br><span style="font-size:{max(18, item.font_size - 4)}px;color:{base.C["muted"]};font-weight:400;">{subtitle}</span></div>'
    return "<br>".join(html.escape(line) for line in lines)


def rewrite_metadata(path: Path) -> None:
    tree = ET.parse(path)
    root = tree.getroot()
    root.set("modified", "2026-08-11T00:00:00.000Z")
    diagram = root.find("diagram")
    if diagram is None:
        raise ValueError("draw.io diagram element not found")
    diagram.set("name", "10 · MENTOR OVERVIEW · HORIZONTAL")
    diagram.set("id", "mentor-overview-v10")
    model = diagram.find("mxGraphModel")
    if model is None:
        raise ValueError("mxGraphModel not found")
    model.set("pageWidth", str(PAGE_W))
    model.set("pageHeight", str(PAGE_H))
    ET.indent(tree, space="  ")
    tree.write(path, encoding="utf-8", xml_declaration=True)


def validate_v6_coverage() -> None:
    expected = {
        "header-accent", "header-title", "aws-cloud", "edge-zone", "lifecycle-note",
        "primary-region", "dr-region", "primary-regional-services", "dr-regional-services",
        "primary-vpc", "dr-vpc", "p-multi-az-lane", "p-az-a", "p-az-c",
        "dr-multi-az-lane", "dr-az-a", "dr-az-c", "p-2a-public", "p-2a-private",
        "p-2a-database", "p-2c-public", "p-2c-private", "p-2c-database",
        "dr-1a-public", "dr-1a-private", "dr-1a-database", "dr-1c-public",
        "dr-1c-private", "dr-1c-database", "primary-data", "dr-data", "dr-note",
        "primary-sg-note", "observability", "local-detail", "local-tools", "route53",
        "cloudfront", "acm", "waf", "iam", "ssm", "ecr", "p-s3", "p-alb",
        "p-bastion", "p-eks", "pod-identity", "p-rds", "p-valkey", "p-efs",
        "dr-s3", "dr-alb", "dr-bastion", "dr-eks", "dr-rds", "dr-valkey",
        "dr-efs", "cloudtrail", "guardduty", "eventbridge", "sns", "cloudwatch",
        "security-s3", "actor", "github", "argocd", "grafana", "waf-viewer",
        "git-repo", "operator-pc",
    }
    actual = {item.box_id for item in base.BOXES}
    if expected != actual:
        raise ValueError(f"v6 coverage mismatch: missing={sorted(expected - actual)} extra={sorted(actual - expected)}")


def validate_model_v10() -> None:
    ids = [item.box_id for item in base.BOXES]
    duplicates = sorted({value for value in ids if ids.count(value) > 1})
    if duplicates:
        raise ValueError(f"duplicate box IDs: {duplicates}")
    by_id = {item.box_id: item for item in base.BOXES}
    missing_endpoints = sorted(
        {value for item in base.EDGES for value in (item.source, item.target) if value not in by_id}
    )
    if missing_endpoints:
        raise ValueError(f"missing edge endpoints: {missing_endpoints}")
    for item in base.BOXES:
        if item.x < 0 or item.y < 0 or item.x + item.w > PAGE_W or item.y + item.h > PAGE_H:
            raise ValueError(f"out-of-page box: {item.box_id}")
        if item.parent in by_id:
            parent = by_id[item.parent]
            inside = (
                parent.x <= item.x
                and parent.y <= item.y
                and item.x + item.w <= parent.x + parent.w
                and item.y + item.h <= parent.y + parent.h
            )
            if not inside:
                raise ValueError(f"child outside parent: {item.box_id} -> {item.parent}")
    for item in base.EDGES:
        for x, y in item.points:
            if not (0 <= x <= PAGE_W and 0 <= y <= PAGE_H):
                raise ValueError(f"out-of-page edge waypoint: {item.edge_id} ({x}, {y})")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--drawio", type=Path, default=HERE / "10_MENTOR_OVERVIEW__HORIZONTAL__v10.drawio")
    parser.add_argument("--preview", type=Path)
    parser.add_argument("--all-flows", action="store_true")
    args = parser.parse_args()

    base.PAGE_W = PAGE_W
    base.PAGE_H = PAGE_H
    base.BOXES.clear()
    base.EDGES.clear()
    base.render_box = render_box_v10
    base.box_style = box_style_v10
    base.html_value = html_value_v10

    base.verify_assets()
    build_boxes()
    build_edges()
    validate_v6_coverage()
    validate_model_v10()
    base.write_drawio(args.drawio)
    rewrite_metadata(args.drawio)

    if args.preview:
        visible = {"layer-request"}
        if args.all_flows:
            visible = {"layer-request", "layer-deployment", "layer-operations", "layer-dr", "layer-observability"}
        base.render_preview(args.preview, visible)
    print(args.drawio)
    if args.preview:
        print(args.preview)


if __name__ == "__main__":
    main()
