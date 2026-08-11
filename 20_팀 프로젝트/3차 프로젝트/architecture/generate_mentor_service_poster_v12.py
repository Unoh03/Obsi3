from __future__ import annotations

import argparse
import base64
import html
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image, ImageDraw

import generate_mentor_full_topology_v9 as base
import generate_mentor_reference_v11 as visual


HERE = Path(__file__).resolve().parent
PAGE_W = 3840
PAGE_H = 2160

# V9 already points at the official AWS Architecture Icon package. V12 adds the
# two official service icons that were previously expressed only as text.
base.ICON_PATHS["kms"] = base.SERVICE_ICONS / "Arch_Security-Identity/64/Arch_AWS-Key-Management-Service_64.png"
base.ICON_PATHS["shield"] = base.SERVICE_ICONS / "Arch_Security-Identity/64/Arch_AWS-Shield_64.png"


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
    font_size: int = 26,
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
            badge=badge,
            font_size=font_size,
            z=z,
        )
    )


def add_edge(
    edge_id: str,
    source: str,
    target: str,
    *,
    layer: str = "layer-summary",
    color: str = base.C["request"],
    label: str = "",
    dashed: bool = False,
    width: int = 5,
    exit_xy: tuple[float, float] = (1.0, 0.5),
    entry_xy: tuple[float, float] = (0.0, 0.5),
    points: list[tuple[int, int]] | None = None,
) -> None:
    base.edge(
        edge_id,
        source,
        target,
        layer,
        color,
        label=label,
        dashed=dashed,
        width=width,
        exit_xy=exit_xy,
        entry_xy=entry_xy,
        points=points,
    )


def icon_size_v12(item: base.Box) -> int:
    return {
        "free-service": 124,
        "free-small": 96,
        "free-resource": 72,
        "external": 72,
    }.get(item.kind, 0)


def image_style_external(item: base.Box) -> str:
    data = base64.b64encode(base.ICON_PATHS[item.icon or "user"].read_bytes()).decode("ascii")
    return (
        "shape=label;rounded=1;arcSize=12;whiteSpace=wrap;html=1;"
        f"image=data:image/png,{data};imageWidth=72;imageHeight=72;"
        "imageAlign=left;imageVerticalAlign=middle;align=center;verticalAlign=middle;spacingLeft=88;"
        f"fillColor={item.fill};strokeColor={item.stroke};strokeWidth=2;"
        f"fontFamily=Malgun Gothic;fontSize={item.font_size};fontStyle=1;shadow=0;"
    )


def box_style_v12(item: base.Box) -> str:
    if item.kind == "external" and item.icon:
        return image_style_external(item)
    if item.kind == "lane":
        return (
            "shape=label;container=0;collapsible=0;rounded=0;whiteSpace=wrap;html=1;"
            "align=left;verticalAlign=top;spacingTop=9;spacingLeft=14;"
            f"fillColor={item.fill};strokeColor=none;fontColor={item.stroke};"
            f"fontFamily=Malgun Gothic;fontSize={item.font_size};fontStyle=1;shadow=0;"
        )
    if item.kind == "az-outline":
        return (
            "shape=label;container=0;collapsible=0;rounded=0;whiteSpace=wrap;html=1;"
            "align=left;verticalAlign=top;spacingTop=8;spacingLeft=12;"
            f"fillColor=none;strokeColor={item.stroke};strokeWidth=2;dashed=1;dashPattern=10 8;"
            f"fontColor={item.stroke};fontFamily=Malgun Gothic;fontSize={item.font_size};fontStyle=1;shadow=0;"
        )
    if item.kind == "status":
        return (
            "rounded=1;arcSize=18;whiteSpace=wrap;html=1;align=center;verticalAlign=middle;"
            f"fillColor={item.fill};strokeColor={item.stroke};strokeWidth=2;"
            f"fontColor={item.stroke};fontFamily=Malgun Gothic;fontSize={item.font_size};fontStyle=1;shadow=0;"
        )
    return visual.box_style_v11(item)


def render_box_v12(canvas: Image.Image, item: base.Box) -> None:
    draw = ImageDraw.Draw(canvas)
    xy = (item.x, item.y, item.x + item.w, item.y + item.h)
    if item.kind == "lane":
        draw.rectangle(xy, fill=item.fill)
        draw.text((item.x + 14, item.y + 10), item.label, font=base.font(item.font_size, True), fill=item.stroke)
        return
    if item.kind == "az-outline":
        base.draw_dashed_rectangle(draw, xy, "#FFFFFF", item.stroke, width=2, dash=12, gap=9, radius=0)
        draw.text((item.x + 12, item.y + 8), item.label, font=base.font(item.font_size, True), fill=item.stroke)
        return
    if item.kind == "status":
        draw.rounded_rectangle(xy, radius=18, fill=item.fill, outline=item.stroke, width=2)
        base.centered_text(draw, xy, item.label, item.font_size, color=item.stroke)
        return
    visual.render_box_v11(canvas, item)


def build_boxes() -> None:
    C = base.C

    # Header: two truth states are explicit without turning the poster into prose.
    add_box("header-accent", "", 0, 0, PAGE_W, 12, "bar", fill="#FF9900", stroke="#FF9900", z=0)
    add_box("title", "3차 프로젝트 AWS 전체 인프라", 48, 25, 1850, 64, "text", font_size=52, z=40)
    add_box("subtitle", "Terraform Source · Mentor Overview · Service-level Architecture", 50, 94, 2150, 38, "text-muted", font_size=25, z=40)
    add_box(
        "source-status",
        "SOURCE DEFAULT · minimal / DR conditional",
        2520,
        32,
        600,
        64,
        "status",
        stroke=C["dr"],
        fill=C["dr_fill"],
        font_size=25,
        z=40,
    )
    add_box(
        "prod-status",
        "PRODUCTION BASELINE · HA / DR always-on",
        3140,
        32,
        650,
        64,
        "status",
        stroke=C["daily"],
        fill=C["daily_fill"],
        font_size=25,
        z=40,
    )

    # External actors are aligned directly above the service they operate.
    add_box("github-repo", "GitHub Repo", 100, 165, 250, 108, "external", icon="source", stroke=C["line"], font_size=26, z=35)
    add_box("github-actions", "GitHub Actions", 390, 165, 280, 108, "external", icon="source", stroke=C["deploy"], font_size=26, z=35)
    add_box("user", "사용자 / 실험자", 820, 165, 285, 108, "external", icon="user", stroke=C["request"], font_size=26, z=35)
    add_box("operator", "운영자 PC\nTerraform · PowerShell", 3190, 155, 420, 125, "external", icon="toolkit", stroke=C["operations"], font_size=25, z=35)

    # One AWS boundary and one sparse shared shelf. No card grid is used here.
    add_box("aws-cloud", "AWS Cloud", 70, 305, 3700, 1655, "group", icon="cloud_group", stroke=C["ink"], fill="#FBFCFD", font_size=38, z=1)
    add_box(
        "shared-services",
        "Shared entry · identity · control",
        120,
        350,
        3600,
        245,
        "group",
        parent="aws-cloud",
        stroke=C["foundation"],
        fill=C["foundation_fill"],
        font_size=34,
        z=2,
    )
    add_box("ecr", "Amazon ECR\nImmutable image", 250, 395, 240, 178, "free-service", parent="shared-services", icon="ecr", stroke=C["foundation"], font_size=28, z=25)
    add_box("route53", "Route 53\nDNS · opt-in", 790, 395, 220, 178, "free-service", parent="shared-services", icon="route53", stroke=C["opt"], badge="OPT", font_size=29, z=25)
    add_box("cloudfront", "CloudFront\nPrimary origin", 1050, 395, 230, 178, "free-service", parent="shared-services", icon="cloudfront", stroke=C["foundation"], font_size=28, z=25)
    add_box("acm", "ACM\nCustom TLS", 1320, 395, 210, 178, "free-service", parent="shared-services", icon="acm", stroke=C["opt"], badge="OPT", font_size=29, z=25)
    add_box("waf", "AWS WAF\nManaged rules · COUNT", 1570, 395, 235, 178, "free-service", parent="shared-services", icon="waf", stroke=C["obs"], font_size=27, z=25)
    add_box("shield", "AWS Shield\nStandard", 1840, 395, 210, 178, "free-service", parent="shared-services", icon="shield", stroke=C["obs"], font_size=29, z=25)
    add_box("iam", "AWS IAM\nGitHub OIDC · Roles", 2390, 395, 235, 178, "free-service", parent="shared-services", icon="iam", stroke=C["foundation"], font_size=27, z=25)
    add_box("ssm", "Systems Manager\nAdd-ons · Bastion", 2670, 395, 245, 178, "free-service", parent="shared-services", icon="ssm", stroke=C["operations"], font_size=27, z=25)
    add_box(
        "foundation-note",
        "Prerequisites · Hosted Zone · EC2 Key Pair\nFoundation state · output contract",
        3000,
        440,
        650,
        82,
        "tag",
        parent="shared-services",
        stroke=C["foundation"],
        font_size=24,
        z=25,
    )

    build_region(
        prefix="p",
        region_id="primary-region",
        region_label="Primary · Seoul · ap-northeast-2",
        region_x=120,
        vpc_id="p-vpc",
        vpc_label="Primary VPC · 10.0.0.0/16",
        az_a="ap-northeast-2a",
        az_c="ap-northeast-2c",
        dr=False,
    )
    build_region(
        prefix="dr",
        region_id="dr-region",
        region_label="DR · Tokyo · ap-northeast-1",
        region_x=2010,
        vpc_id="dr-vpc",
        vpc_label="DR VPC · 10.10.0.0/16",
        az_a="ap-northeast-1a",
        az_c="ap-northeast-1c",
        dr=True,
    )

    # A single, open operations shelf replaces the previous three boxed card grids.
    add_box("observability", "Observability · Detection · Query", 120, 1515, 3600, 405, "group", parent="aws-cloud", stroke=C["obs"], fill=C["obs_fill"], font_size=35, z=2)
    add_box("audit-area", "Audit & Logs", 170, 1570, 1060, 300, "rail", parent="observability", stroke=C["foundation"], fill=C["obs_fill"], font_size=27, z=3)
    add_box("detect-area", "Detection & Alert", 1280, 1570, 1100, 300, "rail", parent="observability", stroke=C["obs"], fill=C["obs_fill"], font_size=27, z=3)
    add_box("query-area", "Query & Response", 2430, 1570, 1235, 300, "rail", parent="observability", stroke=C["operations"], fill=C["obs_fill"], font_size=27, z=3)

    add_box("cloudtrail", "CloudTrail\nAPI audit", 200, 1630, 250, 190, "free-service", parent="audit-area", icon="cloudtrail", stroke=C["foundation"], font_size=28, z=25)
    add_box("cloudwatch", "CloudWatch\nLogs · Alarm · Insights", 500, 1630, 270, 190, "free-service", parent="audit-area", icon="cloudwatch", stroke=C["foundation"], font_size=27, z=25)
    add_box("security-s3", "Security Log S3\nArchive · 30 days", 820, 1630, 270, 190, "free-service", parent="audit-area", icon="s3", stroke=C["foundation"], font_size=27, z=25)

    add_box("guardduty", "GuardDuty\nPrimary detector", 1310, 1630, 250, 190, "free-service", parent="detect-area", icon="guardduty", stroke=C["obs"], font_size=27, z=25)
    add_box("eventbridge", "EventBridge\nFinding route", 1600, 1630, 250, 190, "free-service", parent="detect-area", icon="eventbridge", stroke=C["obs"], font_size=27, z=25)
    add_box("sns", "Amazon SNS\nEmail alert", 1890, 1630, 240, 190, "free-service", parent="detect-area", icon="sns", stroke=C["obs"], font_size=27, z=25)
    add_box("alarm", "Metric Filter · Alarm", 2140, 1690, 210, 72, "tag", parent="detect-area", stroke=C["obs"], font_size=22, z=25)

    add_box("athena", "Amazon Athena\nSecurity Log SQL", 2470, 1630, 260, 190, "free-service", parent="query-area", icon="athena", stroke=C["operations"], font_size=27, z=25)
    add_box("query-note", "CloudWatch Logs Insights\nSecurity review · Evidence", 2780, 1670, 390, 105, "tag", parent="query-area", stroke=C["operations"], font_size=25, z=25)

    # Local tools are explicitly outside the AWS boundary.
    add_box("local-tools", "AWS 외부 · Local response tools", 800, 1980, 2240, 150, "group", stroke=C["line"], fill="#FFFFFF", dashed=True, font_size=29, z=2)
    add_box("grafana", "Local Docker Grafana\nAthena / S3", 900, 2015, 520, 100, "external", parent="local-tools", icon="server", stroke=C["operations"], font_size=26, z=25)
    add_box("waf-viewer", "WAF Live Viewer\nCloudWatch Live Tail", 1640, 2015, 540, 100, "external", parent="local-tools", icon="toolkit", stroke=C["obs"], font_size=26, z=25)
    add_box("evidence", "Evidence Bundle\nSanitized · SHA-256", 2380, 2015, 520, 100, "external", parent="local-tools", icon="source", stroke=C["foundation"], font_size=26, z=25)


def build_region(
    *,
    prefix: str,
    region_id: str,
    region_label: str,
    region_x: int,
    vpc_id: str,
    vpc_label: str,
    az_a: str,
    az_c: str,
    dr: bool,
) -> None:
    C = base.C
    region_stroke = C["dr"] if dr else C["network"]
    region_fill = "#FFFFFF"
    badge = "DR profile" if dr else None
    dashed = dr
    x = region_x

    add_box(region_id, region_label, x, 625, 1710, 850, "group", parent="aws-cloud", icon="region_group", stroke=region_stroke, fill=region_fill, dashed=dashed, badge=badge, font_size=34, z=2)

    s3_id = "dr-app-s3" if dr else "p-app-s3"
    s3_label = "Application S3\nCRR target · DR" if dr else "Application S3\nAccess opt-in"
    s3_x = x + 30 if dr else x + 1450
    add_box(s3_id, s3_label, s3_x, 680, 225, 142, "free-small", parent=region_id, icon="s3", stroke=C["dr"] if dr else C["opt"], badge="DR" if dr else "OPT", font_size=26, z=25)

    vpc_x = x + 40
    add_box(vpc_id, vpc_label, vpc_x, 830, 1630, 640, "group", parent=region_id, icon="vpc_group", stroke=C["dr"], fill="#FFFFFF", dashed=dr, font_size=31, z=3)

    igw_x = x + (980 if dr else 520)
    add_box(f"{prefix}-igw", "IGW", igw_x, 715, 210, 110, "free-resource", parent=region_id, icon="igw", stroke=C["network"] if not dr else C["dr"], font_size=24, z=25)

    # AZ outlines and subnet lanes are background coordinates, not service cards.
    add_box(f"{prefix}-az-a", az_a, x + 70, 915, 780, 525, "az-outline", parent=vpc_id, stroke=region_stroke, font_size=25, z=4)
    add_box(f"{prefix}-az-c", az_c, x + 890, 915, 770, 525, "az-outline", parent=vpc_id, stroke=region_stroke, font_size=25, z=4)
    add_box(f"{prefix}-public-lane", "PUBLIC", x + 85, 955, 1580, 125, "lane", parent=vpc_id, stroke=C["opt"], fill=C["public_fill"], font_size=24, z=5)
    add_box(f"{prefix}-private-lane", "PRIVATE", x + 85, 1090, 1580, 200, "lane", parent=vpc_id, stroke=C["network"], fill=C["private_fill"], font_size=24, z=5)
    add_box(f"{prefix}-data-lane", "DATA", x + 85, 1300, 1580, 160, "lane", parent=vpc_id, stroke=C["dr"], fill=C["data_fill"], font_size=24, z=5)

    add_box(f"{prefix}-bastion", "Bastion", x + 210, 960, 190, 115, "free-resource", parent=vpc_id, icon="ec2", stroke=C["dr"] if dr else C["daily"], badge="DR" if dr else None, font_size=24, z=25)
    add_box(f"{prefix}-nat", "NAT · single", x + 440, 960, 190, 115, "free-resource", parent=vpc_id, icon="nat", stroke=C["dr"] if dr else C["daily"], font_size=24, z=25)
    add_box(f"{prefix}-alb", "ALB · Multi-AZ", x + 740, 950, 230, 130, "free-small", parent=vpc_id, icon="alb", stroke=C["dr"] if dr else C["daily"], badge="DR" if dr else None, font_size=25, z=25)

    eks_id = f"{prefix}-eks"
    add_box(eks_id, "Amazon EKS · Private API · 2 AZ capacity" if not dr else "Amazon EKS · Warm standby profile", x + 180, 1105, 1350, 170, "eks-group", parent=vpc_id, stroke=C["dr"] if dr else C["daily"], fill=C["dr_fill"] if dr else "#FFFDFC", dashed=dr, badge="DR" if dr else None, font_size=29, z=10)
    add_box(f"{prefix}-eks-icon", "", x + 210, 1145, 165, 115, "free-small", parent=eks_id, icon="eks", stroke=C["dr"] if dr else C["daily"], font_size=24, z=25)
    add_box(f"{prefix}-pod-identity", "Pod Identity", x + 400, 1145, 190, 115, "free-resource", parent=eks_id, icon="iam", stroke=C["dr"] if dr else C["foundation"], font_size=24, z=25)
    runtime_label = "System Node · Karpenter + interruption queue" if not dr else "System Node · Karpenter · DR profile"
    workload_label = "Argo CD · BANK DVWA · LBC · CoreDNS · Fluent Bit" if not dr else "Argo CD opt-in · DVWA bootstrap · LBC · DNS · Fluent Bit"
    add_box(f"{prefix}-eks-runtime", runtime_label, x + 620, 1145, 850, 50, "tag", parent=eks_id, stroke=C["dr"] if dr else C["daily"], font_size=24, z=25)
    add_box(f"{prefix}-eks-workload", workload_label, x + 620, 1205, 850, 50, "tag", parent=eks_id, stroke=C["dr"] if dr else C["deploy"], font_size=23, z=25)

    if dr:
        add_box("dr-rds", "RDS Replica\nCross-Region", x + 65, 1310, 240, 150, "free-small", parent=vpc_id, icon="rds", stroke=C["dr"], badge="DR", font_size=26, z=25)
        add_box("dr-kms", "KMS · DR key", x + 350, 1315, 190, 140, "free-resource", parent=vpc_id, icon="kms", stroke=C["dr"], font_size=24, z=25)
        add_box("dr-valkey", "Valkey\nIndependent · opt-in", x + 870, 1310, 240, 150, "free-small", parent=vpc_id, icon="valkey", stroke=C["opt"], badge="OPT", font_size=25, z=25)
        add_box("dr-efs", "Amazon EFS\nIndependent · opt-in", x + 1310, 1310, 240, 150, "free-small", parent=vpc_id, icon="efs", stroke=C["opt"], badge="OPT", font_size=25, z=25)
    else:
        add_box("p-efs", "Amazon EFS\n2 AZ · opt-in", x + 210, 1310, 240, 150, "free-small", parent=vpc_id, icon="efs", stroke=C["opt"], badge="OPT", font_size=25, z=25)
        add_box("p-valkey", "Valkey\nIndependent · opt-in", x + 650, 1310, 240, 150, "free-small", parent=vpc_id, icon="valkey", stroke=C["opt"], badge="OPT", font_size=25, z=25)
        add_box("p-rds", "RDS MariaDB\nS-AZ / M-AZ", x + 1410, 1310, 240, 150, "free-small", parent=vpc_id, icon="rds", stroke=C["daily"], font_size=26, z=25)


def build_edges() -> None:
    C = base.C

    # Default-visible poster flow: exactly twelve connectors.
    add_edge("req-user-dns", "user", "route53", label="HTTPS / DNS", exit_xy=(0.5, 1.0), entry_xy=(0.5, 0.0), points=[(962, 320), (900, 320)])
    add_edge("req-dns-edge", "route53", "cloudfront", label="Alias", exit_xy=(1.0, 0.5), entry_xy=(0.0, 0.5))
    add_edge("req-edge-alb", "cloudfront", "p-alb", label="Origin :80", exit_xy=(0.5, 1.0), entry_xy=(0.5, 0.0), points=[(1165, 610), (975, 610), (975, 935)])
    add_edge("req-alb-eks", "p-alb", "p-eks", label="Pod IP :80", exit_xy=(0.5, 1.0), entry_xy=(0.5, 0.0))
    add_edge("req-eks-rds", "p-eks", "p-rds", label="MariaDB", exit_xy=(0.95, 1.0), entry_xy=(0.5, 0.0), points=[(1590, 1295), (1650, 1295)])

    add_edge("dep-repo-actions", "github-repo", "github-actions", color=C["deploy"], width=4)
    add_edge("dep-actions-ecr", "github-actions", "ecr", color=C["deploy"], label="Build · Push", exit_xy=(0.5, 1.0), entry_xy=(0.5, 0.0), points=[(530, 315), (370, 315)])
    add_edge("dep-ecr-eks", "ecr", "p-eks", color=C["deploy"], label="Argo CD sync", exit_xy=(0.5, 1.0), entry_xy=(0.0, 0.5), points=[(140, 610), (140, 1190)])

    add_edge("dr-s3-crr", "p-app-s3", "dr-app-s3", color=C["replication"], label="S3 CRR", dashed=True, width=5)
    add_edge("dr-rds-replica", "p-rds", "dr-rds", color=C["replication"], label="Cross-Region replica", dashed=True, width=5)

    add_edge("det-finding", "guardduty", "eventbridge", color=C["telemetry"], label="Finding", width=4)
    add_edge("det-alert", "eventbridge", "sns", color=C["telemetry"], label="Alert", width=4)

    # Optional detail layer: available for mentor questions, hidden by default.
    add_edge("detail-acm", "acm", "cloudfront", layer="layer-detail", color=C["request"], label="TLS", dashed=True, width=3, exit_xy=(0.5, 0.0), entry_xy=(0.5, 0.0), points=[(1425, 365), (1165, 365)])
    add_edge("detail-waf", "waf", "cloudfront", layer="layer-detail", color=C["telemetry"], label="Web ACL", dashed=True, width=3, exit_xy=(0.0, 0.5), entry_xy=(1.0, 0.5))
    add_edge("detail-oidc", "github-actions", "iam", layer="layer-detail", color=C["deploy"], label="Assume role", dashed=True, width=3, exit_xy=(0.5, 0.0), entry_xy=(0.5, 0.0), points=[(530, 140), (2507, 140), (2507, 380)])
    add_edge("detail-operator-ssm", "operator", "ssm", layer="layer-detail", color=C["operations"], label="Run Command", dashed=True, width=3, exit_xy=(0.5, 1.0), entry_xy=(0.5, 0.0))
    add_edge("detail-ssm-primary", "ssm", "p-bastion", layer="layer-detail", color=C["operations"], label="Association", dashed=True, width=3, exit_xy=(0.5, 1.0), entry_xy=(0.5, 0.0), points=[(2792, 610), (425, 610), (425, 910)])
    add_edge("detail-ssm-dr", "ssm", "dr-bastion", layer="layer-detail", color=C["operations"], label="DR ops", dashed=True, width=3, exit_xy=(0.5, 1.0), entry_xy=(0.5, 0.0), points=[(2792, 610), (2315, 610), (2315, 910)])
    add_edge("detail-athena-grafana", "athena", "grafana", layer="layer-detail", color=C["operations"], label="Dashboard", dashed=True, width=3, exit_xy=(0.5, 1.0), entry_xy=(0.5, 0.0), points=[(2600, 1940), (1160, 1940), (1160, 2000)])
    add_edge("detail-cloudwatch-viewer", "cloudwatch", "waf-viewer", layer="layer-detail", color=C["operations"], label="Live Tail", dashed=True, width=3, exit_xy=(0.5, 1.0), entry_xy=(0.5, 0.0), points=[(635, 1940), (1910, 1940), (1910, 2000)])


PRESENTATION_ONLY = {
    "header-accent",
    "title",
    "subtitle",
    "legend-foundation",
    "legend-daily",
    "legend-dr",
    "legend-opt",
    "legend-layer",
}


EXPLICIT_V9_COVERAGE = {
    "global-foundation": "shared-services",
    "edge-area": "shared-services",
    "platform-area": "shared-services",
    "hosted-zone": "foundation-note",
    "key-pair": "foundation-note",
    "foundation-state": "foundation-note",
    "dr-log-group": "cloudwatch",
    "p-flow": "cloudwatch",
    "p-eks-box": "p-eks",
    "p-eks-api": "p-eks-icon",
    "p-system-node": "p-eks-runtime",
    "p-karpenter": "p-eks-runtime",
    "p-addons": "p-eks-workload",
    "p-pod-identity": "p-pod-identity",
    "p-argo": "p-eks-workload",
    "p-dvwa": "p-eks-workload",
    "dr-eks-box": "dr-eks",
    "dr-eks-api": "dr-eks-icon",
    "dr-system-node": "dr-eks-runtime",
    "dr-karpenter": "dr-eks-runtime",
    "dr-addons": "dr-eks-workload",
    "dr-pod-identity": "dr-pod-identity",
    "dr-argo": "dr-eks-workload",
    "dr-dvwa": "dr-eks-workload",
    "alarm": "cloudwatch",
    "logs-insights": "cloudwatch",
    "security-review": "query-note",
    "runtime-note": "source-status",
}


def v9_coverage_target(source_id: str, actual_ids: set[str]) -> str | None:
    if source_id in PRESENTATION_ONLY:
        return "presentation"
    if source_id in actual_ids:
        return source_id
    if source_id in EXPLICIT_V9_COVERAGE:
        return EXPLICIT_V9_COVERAGE[source_id]
    for prefix, target in [
        ("p-public-", "p-public-lane"),
        ("p-private-", "p-private-lane"),
        ("p-data-", "p-data-lane"),
        ("dr-public-", "dr-public-lane"),
        ("dr-private-", "dr-private-lane"),
        ("dr-data-", "dr-data-lane"),
    ]:
        if source_id.startswith(prefix):
            return target
    return None


def validate_model(source_v9_ids: set[str]) -> None:
    actual_ids = {item.box_id for item in base.BOXES}
    duplicates = sorted({item.box_id for item in base.BOXES if sum(1 for value in base.BOXES if value.box_id == item.box_id) > 1})
    if duplicates:
        raise ValueError(f"duplicate box ids: {duplicates}")

    required_services = {
        "route53",
        "acm",
        "cloudfront",
        "waf",
        "shield",
        "iam",
        "ssm",
        "ecr",
        "p-alb",
        "p-eks",
        "p-pod-identity",
        "p-rds",
        "p-valkey",
        "p-efs",
        "p-app-s3",
        "dr-alb",
        "dr-eks",
        "dr-pod-identity",
        "dr-rds",
        "dr-kms",
        "dr-valkey",
        "dr-efs",
        "dr-app-s3",
        "cloudtrail",
        "cloudwatch",
        "security-s3",
        "guardduty",
        "eventbridge",
        "sns",
        "athena",
        "grafana",
        "waf-viewer",
    }
    missing_required = sorted(required_services - actual_ids)
    if missing_required:
        raise ValueError(f"missing required service sets: {missing_required}")

    by_id = {item.box_id: item for item in base.BOXES}
    for item in base.BOXES:
        if item.x < 0 or item.y < 0 or item.x + item.w > PAGE_W or item.y + item.h > PAGE_H:
            raise ValueError(f"out-of-page box: {item.box_id}")
        if item.parent in by_id:
            parent = by_id[item.parent]
            if not (
                parent.x <= item.x
                and parent.y <= item.y
                and item.x + item.w <= parent.x + parent.w
                and item.y + item.h <= parent.y + parent.h
            ):
                raise ValueError(f"child outside parent: {item.box_id} -> {item.parent}")

    summary_edges = [item for item in base.EDGES if item.layer == "layer-summary"]
    if len(summary_edges) != 12:
        raise ValueError(f"summary connector budget changed: {len(summary_edges)}")
    for item in base.EDGES:
        if item.source not in by_id or item.target not in by_id:
            raise ValueError(f"missing edge endpoint: {item.edge_id}")
        for x, y in item.points:
            if not (0 <= x <= PAGE_W and 0 <= y <= PAGE_H):
                raise ValueError(f"out-of-page edge waypoint: {item.edge_id} ({x}, {y})")

    foreground_kinds = {"free-service", "free-small", "free-resource", "external", "status"}
    for item in base.BOXES:
        if item.kind in foreground_kinds and item.font_size < 22:
            raise ValueError(f"small foreground label: {item.box_id} ({item.font_size})")

    uncovered_v9 = sorted(source_id for source_id in source_v9_ids if v9_coverage_target(source_id, actual_ids) is None)
    if uncovered_v9:
        raise ValueError(f"V9 semantic coverage missing: {uncovered_v9}")
    invalid_targets = sorted(
        {
            target
            for source_id in source_v9_ids
            if (target := v9_coverage_target(source_id, actual_ids)) not in actual_ids and target != "presentation"
        }
    )
    if invalid_targets:
        raise ValueError(f"V9 coverage points to missing V12 targets: {invalid_targets}")


def html_value_v12(item: base.Box) -> str:
    if item.kind == "lane":
        return html.escape(item.label)
    return visual.html_value_v11(item)


def add_drawio_edge(root: ET.Element, item: base.Edge) -> None:
    font_size = 22 if item.layer == "layer-summary" else 18
    style = (
        "edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;"
        f"strokeWidth={item.width};strokeColor={item.color};endArrow=block;endFill=1;"
        f"fontFamily=Malgun Gothic;fontSize={font_size};fontStyle=1;labelBackgroundColor={base.C['white']};"
        f"exitX={item.exit_xy[0]};exitY={item.exit_xy[1]};entryX={item.entry_xy[0]};entryY={item.entry_xy[1]};"
        "exitDx=0;exitDy=0;entryDx=0;entryDy=0;"
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
    diagram = ET.SubElement(mxfile, "diagram", {"name": "12 · MENTOR OVERVIEW · SERVICE POSTER", "id": "mentor-service-poster-v12"})
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
    for layer_id, label, visible in [
        ("layer-summary", "01 · Mentor Summary Flow", True),
        ("layer-detail", "02 · Optional Detail Relations", False),
        ("layer-topology", "00 · Full Infrastructure", True),
    ]:
        attrs = {"id": layer_id, "value": label, "parent": "0"}
        if not visible:
            attrs["visible"] = "0"
        ET.SubElement(root, "mxCell", attrs)

    by_id = {item.box_id: item for item in base.BOXES}
    for item in base.EDGES:
        add_drawio_edge(root, item)
    for item in base.BOXES:
        base.add_vertex(root, item, by_id)
        base.add_badge_vertex(root, item, by_id)

    ET.indent(mxfile, space="  ")
    path.write_text('<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(mxfile, encoding="unicode"), encoding="utf-8", newline="\n")


def render_preview(path: Path) -> None:
    canvas = Image.new("RGBA", (PAGE_W, PAGE_H), base.rgb(base.C["bg"]) + (255,))
    by_id = {item.box_id: item for item in base.BOXES}
    ordered = sorted(base.BOXES, key=lambda value: value.z)
    for item in (value for value in ordered if value.z <= 10):
        render_box_v12(canvas, item)

    draw = ImageDraw.Draw(canvas)
    for item in base.EDGES:
        if item.layer != "layer-summary":
            continue
        points = base.edge_points(item, by_id)
        if item.dashed:
            base.dashed_polyline(draw, points, item.color, item.width)
        else:
            draw.line(points, fill=item.color, width=item.width, joint="curve")
        base.arrowhead(draw, points[-2], points[-1], item.color, max(16, item.width * 4))
        if item.label:
            mid = points[len(points) // 2]
            f = base.font(21, True)
            bounds = draw.textbbox((0, 0), item.label, font=f)
            tw = bounds[2] - bounds[0]
            th = bounds[3] - bounds[1]
            draw.rounded_rectangle((mid[0] - tw / 2 - 8, mid[1] - th / 2 - 6, mid[0] + tw / 2 + 8, mid[1] + th / 2 + 6), radius=6, fill="#FFFFFF")
            draw.text((mid[0] - tw / 2, mid[1] - th / 2), item.label, font=f, fill=item.color)

    for item in (value for value in ordered if value.z > 10):
        render_box_v12(canvas, item)
    path.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(path, quality=96)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--drawio", type=Path, default=HERE / "12_MENTOR_OVERVIEW__SERVICE_POSTER__v12.drawio")
    parser.add_argument("--preview", type=Path)
    args = parser.parse_args()

    # Capture the previous full topology as a semantic coverage ledger only.
    base.BOXES.clear()
    base.EDGES.clear()
    base.build_boxes()
    source_v9_ids = {item.box_id for item in base.BOXES}

    base.PAGE_W = PAGE_W
    base.PAGE_H = PAGE_H
    base.BOXES.clear()
    base.EDGES.clear()
    visual.PAGE_W = PAGE_W
    visual.PAGE_H = PAGE_H
    visual.icon_size = icon_size_v12
    base.box_style = box_style_v12
    base.html_value = html_value_v12

    base.verify_assets()
    build_boxes()
    build_edges()
    validate_model(source_v9_ids)
    write_drawio(args.drawio)
    if args.preview:
        render_preview(args.preview)

    print(f"drawio={args.drawio}")
    print(f"v12_boxes={len(base.BOXES)}")
    print(f"summary_edges={sum(1 for item in base.EDGES if item.layer == 'layer-summary')}")
    print(f"detail_edges={sum(1 for item in base.EDGES if item.layer == 'layer-detail')}")
    print(f"v9_coverage={len(source_v9_ids)}/{len(source_v9_ids)}")
    if args.preview:
        print(f"preview={args.preview}")


if __name__ == "__main__":
    main()
