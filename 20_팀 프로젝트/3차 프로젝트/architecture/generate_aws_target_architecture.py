from __future__ import annotations

import base64
import math
import tempfile
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


OUTPUT_DIR = Path(__file__).resolve().parent
ICON_CACHE_DIR = Path(tempfile.gettempdir()) / "codex-aws-icons-04302026"
ICON_ARCHIVE = Path(tempfile.gettempdir()) / "codex-aws-icons-04302026.zip"
ICON_ROOT = ICON_CACHE_DIR / "Architecture-Service-Icons_04302026"

AWS_ICON_PACKAGE = (
    "https://d1.awsstatic.com/onedam/marketing-channels/website/aws/en_US/"
    "architecture/approved/architecture-icons/"
    "Icon-package_04302026.4705b90f5aa45b019271a2699e9ce9b97b941ee1.zip"
)

FONT_REGULAR = Path(r"C:\Windows\Fonts\malgun.ttf")
FONT_BOLD = Path(r"C:\Windows\Fonts\malgunbd.ttf")

COLORS = {
    "bg": "#F4F6F8",
    "card": "#FFFFFF",
    "ink": "#232F3E",
    "muted": "#5F6B7A",
    "border": "#D5DBDB",
    "orange": "#FF9900",
    "orange_light": "#FFF4E5",
    "blue": "#147EBA",
    "blue_light": "#EAF5FB",
    "red": "#D13212",
    "red_light": "#FFF0ED",
    "green": "#1D8102",
    "green_light": "#ECF7E8",
    "purple": "#8C4FFF",
    "purple_light": "#F4F0FF",
    "teal": "#00A4A6",
    "teal_light": "#EAF9F7",
    "gray_light": "#F7F8F8",
    "magenta": "#E7157B",
}

ICON_PATHS = {
    "route53": ("Arch_Networking-Content-Delivery", "Arch_Amazon-Route-53_64.png"),
    "cloudfront": ("Arch_Networking-Content-Delivery", "Arch_Amazon-CloudFront_64.png"),
    "waf": ("Arch_Security-Identity", "Arch_AWS-WAF_64.png"),
    "alb": ("Arch_Networking-Content-Delivery", "Arch_Elastic-Load-Balancing_64.png"),
    "eks": ("Arch_Containers", "Arch_Amazon-Elastic-Kubernetes-Service_64.png"),
    "ecr": ("Arch_Containers", "Arch_Amazon-Elastic-Container-Registry_64.png"),
    "rds": ("Arch_Databases", "Arch_Amazon-RDS_64.png"),
    "efs": ("Arch_Storage", "Arch_Amazon-EFS_64.png"),
    "s3": ("Arch_Storage", "Arch_Amazon-Simple-Storage-Service_64.png"),
    "cloudwatch": ("Arch_Management-Tools", "Arch_Amazon-CloudWatch_64.png"),
    "cloudtrail": ("Arch_Management-Tools", "Arch_AWS-CloudTrail_64.png"),
    "guardduty": ("Arch_Security-Identity", "Arch_Amazon-GuardDuty_64.png"),
    "iam": (
        "Arch_Security-Identity",
        "Arch_AWS-Identity-and-Access-Management_64.png",
    ),
    "inspector": ("Arch_Security-Identity", "Arch_Amazon-Inspector_64.png"),
}


def icon_file(key: str) -> Path:
    category, filename = ICON_PATHS[key]
    return ICON_ROOT / category / "64" / filename


def ensure_icon_package() -> None:
    if all(icon_file(key).exists() for key in ICON_PATHS):
        return
    ICON_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    if not ICON_ARCHIVE.exists():
        urllib.request.urlretrieve(AWS_ICON_PACKAGE, ICON_ARCHIVE)
    with zipfile.ZipFile(ICON_ARCHIVE) as archive:
        archive.extractall(ICON_CACHE_DIR)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_BOLD if bold else FONT_REGULAR), size)


def rounded(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    fill: str,
    outline: str = COLORS["border"],
    width: int = 2,
    radius: int = 18,
) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def center_text(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    text: str,
    size: int = 22,
    color: str = COLORS["ink"],
    bold: bool = False,
    spacing: int = 5,
) -> None:
    x1, y1, x2, y2 = box
    fnt = font(size, bold)
    bounds = draw.multiline_textbbox(
        (0, 0), text, font=fnt, spacing=spacing, align="center"
    )
    w = bounds[2] - bounds[0]
    h = bounds[3] - bounds[1]
    draw.multiline_text(
        ((x1 + x2 - w) / 2, (y1 + y2 - h) / 2),
        text,
        font=fnt,
        fill=color,
        spacing=spacing,
        align="center",
    )


def header(
    draw: ImageDraw.ImageDraw,
    title: str,
    subtitle: str,
    badge: str,
) -> None:
    draw.text((60, 40), title, font=font(38, True), fill=COLORS["ink"])
    draw.text((62, 92), subtitle, font=font(19), fill=COLORS["muted"])
    badge_box = (1535, 48, 1855, 96)
    rounded(draw, badge_box, COLORS["orange_light"], COLORS["orange"], 2, 22)
    center_text(draw, badge_box, badge, 16, COLORS["ink"], True)


def group(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    title: str,
    accent: str,
    fill: str = COLORS["card"],
    title_size: int = 21,
) -> None:
    rounded(draw, box, fill, accent, 3, 20)
    draw.text(
        (box[0] + 20, box[1] + 16),
        title,
        font=font(title_size, True),
        fill=accent,
    )


def paste_icon(
    canvas: Image.Image,
    key: str,
    center: tuple[int, int],
    size: int = 64,
) -> None:
    icon = Image.open(icon_file(key)).convert("RGBA")
    icon = icon.resize((size, size), Image.Resampling.LANCZOS)
    canvas.alpha_composite(icon, (center[0] - size // 2, center[1] - size // 2))


def service_tile(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    key: str,
    label: str,
    note: str = "",
    accent: str = COLORS["border"],
    fill: str = COLORS["card"],
    icon_size: int = 56,
) -> None:
    rounded(draw, box, fill, accent, 2, 16)
    cx = (box[0] + box[2]) // 2
    paste_icon(canvas, key, (cx, box[1] + 52), icon_size)
    draw.text(
        (cx, box[1] + 92),
        label,
        font=font(18, True),
        fill=COLORS["ink"],
        anchor="ma",
        align="center",
    )
    if note:
        draw.text(
            (cx, box[1] + 122),
            note,
            font=font(13),
            fill=COLORS["muted"],
            anchor="ma",
            align="center",
        )


def node(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    label: str,
    fill: str,
    accent: str,
    size: int = 18,
) -> None:
    rounded(draw, box, fill, accent, 2, 14)
    center_text(draw, box, label, size, COLORS["ink"], True)


def dashed_line(
    draw: ImageDraw.ImageDraw,
    start: tuple[int, int],
    end: tuple[int, int],
    color: str,
    width: int = 4,
    dash: int = 14,
    gap: int = 9,
) -> None:
    distance = math.dist(start, end)
    if distance == 0:
        return
    ux = (end[0] - start[0]) / distance
    uy = (end[1] - start[1]) / distance
    pos = 0.0
    while pos < distance:
        finish = min(pos + dash, distance)
        draw.line(
            (
                start[0] + ux * pos,
                start[1] + uy * pos,
                start[0] + ux * finish,
                start[1] + uy * finish,
            ),
            fill=color,
            width=width,
        )
        pos += dash + gap


def arrow(
    draw: ImageDraw.ImageDraw,
    start: tuple[int, int],
    end: tuple[int, int],
    color: str,
    width: int = 5,
    dashed: bool = False,
) -> None:
    if dashed:
        dashed_line(draw, start, end, color, width)
    else:
        draw.line((*start, *end), fill=color, width=width)
    angle = math.atan2(end[1] - start[1], end[0] - start[0])
    size = 17
    p1 = (
        end[0] - size * math.cos(angle - math.pi / 6),
        end[1] - size * math.sin(angle - math.pi / 6),
    )
    p2 = (
        end[0] - size * math.cos(angle + math.pi / 6),
        end[1] - size * math.sin(angle + math.pi / 6),
    )
    draw.polygon((end, p1, p2), fill=color)


def orthogonal_arrow(
    draw: ImageDraw.ImageDraw,
    points: list[tuple[int, int]],
    color: str,
    width: int = 5,
) -> None:
    for start, end in zip(points, points[1:]):
        draw.line((*start, *end), fill=color, width=width)
    arrow(draw, points[-2], points[-1], color, width)


def step_badge(
    draw: ImageDraw.ImageDraw,
    center: tuple[int, int],
    number: int,
    color: str,
) -> None:
    draw.ellipse(
        (center[0] - 17, center[1] - 17, center[0] + 17, center[1] + 17),
        fill=color,
    )
    draw.text(
        center,
        str(number),
        font=font(16, True),
        fill=COLORS["card"],
        anchor="mm",
    )


def legend_item(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    label: str,
    color: str,
    dashed: bool = False,
) -> None:
    if dashed:
        dashed_line(draw, (x, y), (x + 55, y), color, 4, 10, 7)
    else:
        draw.line((x, y, x + 55, y), fill=color, width=4)
    draw.text((x + 68, y), label, font=font(15), fill=COLORS["muted"], anchor="lm")


def draw_executive_png(path: Path) -> None:
    canvas = Image.new("RGBA", (1920, 1080), COLORS["bg"])
    draw = ImageDraw.Draw(canvas)
    header(
        draw,
        "3차 프로젝트 · Security Architecture",
        "공격 경로와 탐지·조치·동일 조건 재검증을 한 장에 표시",
        "TARGET · 발표용 핵심 View",
    )

    group(draw, (50, 150, 1870, 575), "Attack Path · 무엇을 검증하는가", COLORS["red"])

    cards = [
        ((90, 225, 330, 500), "접근 주체", COLORS["blue"]),
        ((390, 225, 690, 500), "공개 진입점", COLORS["purple"]),
        ((750, 225, 1080, 500), "EKS Test Workload", COLORS["orange"]),
        ((1140, 225, 1430, 500), "권한 경계", COLORS["magenta"]),
        ((1490, 225, 1810, 500), "보호 대상", COLORS["green"]),
    ]
    for box, title, accent in cards:
        group(draw, box, title, accent, COLORS["card"], 18)

    node(draw, (115, 285, 305, 350), "정상 사용자", COLORS["blue_light"], COLORS["blue"], 17)
    node(
        draw,
        (115, 385, 305, 460),
        "통제된 공격 Runner\n허용 IP · Test Window",
        COLORS["red_light"],
        COLORS["red"],
        15,
    )

    service_tile(
        canvas,
        draw,
        (415, 280, 530, 455),
        "route53",
        "Route 53",
        "DNS",
        COLORS["purple"],
    )
    service_tile(
        canvas,
        draw,
        (545, 280, 665, 455),
        "alb",
        "ALB",
        "Public endpoint",
        COLORS["purple"],
    )
    paste_icon(canvas, "waf", (625, 260), 46)
    draw.text(
        (625, 225),
        "WAF Association",
        font=font(13, True),
        fill=COLORS["red"],
        anchor="ma",
    )

    paste_icon(canvas, "eks", (825, 335), 72)
    node(
        draw,
        (895, 280, 1050, 350),
        "취약 Pod",
        COLORS["red_light"],
        COLORS["red"],
        17,
    )
    node(
        draw,
        (895, 380, 1050, 455),
        "ServiceAccount\nToken·Metadata",
        COLORS["orange_light"],
        COLORS["orange"],
        14,
    )

    service_tile(
        canvas,
        draw,
        (1170, 280, 1285, 455),
        "iam",
        "IAM Role",
        "Pod Identity / IRSA",
        COLORS["magenta"],
    )
    node(
        draw,
        (1300, 300, 1405, 435),
        "과권한·신뢰\n정책 오구성",
        COLORS["red_light"],
        COLORS["red"],
        15,
    )

    service_tile(
        canvas,
        draw,
        (1520, 275, 1660, 460),
        "s3",
        "Amazon S3",
        "민감 데이터 Target",
        COLORS["green"],
    )
    node(
        draw,
        (1680, 305, 1780, 430),
        "RDS 등\n후보 Target",
        COLORS["gray_light"],
        COLORS["border"],
        14,
    )

    for number, start, end in [
        (1, (330, 410), (390, 410)),
        (2, (690, 410), (750, 410)),
        (3, (1080, 410), (1140, 410)),
        (4, (1430, 410), (1490, 410)),
    ]:
        arrow(draw, start, end, COLORS["red"], 5)
        step_badge(draw, ((start[0] + end[0]) // 2, 378), number, COLORS["red"])

    group(
        draw,
        (50, 610, 1870, 990),
        "Detect → Remediate → Retest · 무엇을 증명하는가",
        COLORS["orange"],
    )
    node(
        draw,
        (90, 700, 405, 875),
        "5  Log Sources\n\nWAF·ALB Access Log\nEKS Audit Log\nCloudTrail·VPC Flow Log",
        COLORS["orange_light"],
        COLORS["orange"],
        17,
    )
    service_tile(
        canvas,
        draw,
        (460, 690, 615, 875),
        "cloudwatch",
        "CloudWatch",
        "검색·경보",
        COLORS["magenta"],
    )
    service_tile(
        canvas,
        draw,
        (680, 690, 835, 875),
        "s3",
        "S3 Evidence",
        "원본 증거 보존",
        COLORS["green"],
    )
    node(
        draw,
        (930, 700, 1210, 875),
        "6  Before / After\n\n탐지 여부 · 차단 여부\n피해 범위 · 재현성",
        COLORS["blue_light"],
        COLORS["blue"],
        17,
    )
    node(
        draw,
        (1290, 700, 1510, 875),
        "7  조치 버전 배포\n\nIAM·Manifest·Image\nDetection Rule",
        COLORS["green_light"],
        COLORS["green"],
        16,
    )
    node(
        draw,
        (1600, 700, 1825, 875),
        "8  동일 조건 재실행\n\n같은 입력·같은 절차\n같은 관찰 지점",
        COLORS["purple_light"],
        COLORS["purple"],
        16,
    )

    for start, end, color in [
        ((405, 787), (460, 787), COLORS["orange"]),
        ((615, 787), (680, 787), COLORS["orange"]),
        ((835, 787), (930, 787), COLORS["orange"]),
        ((1210, 787), (1290, 787), COLORS["green"]),
        ((1510, 787), (1600, 787), COLORS["green"]),
    ]:
        arrow(draw, start, end, color, 5)

    draw.text(
        (90, 930),
        "핵심 주장: 공격 성공 자체가 아니라, 진입 → 권한 → 데이터 흐름과 탐지·조치·재검증을 증거로 설명한다.",
        font=font(17, True),
        fill=COLORS["ink"],
    )

    legend_item(draw, 1030, 940, "공격 경로", COLORS["red"])
    legend_item(draw, 1240, 940, "Log·Evidence", COLORS["orange"], True)
    legend_item(draw, 1485, 940, "조치·재검증", COLORS["green"])

    canvas.convert("RGB").save(path, quality=96)


def draw_runtime_png(path: Path) -> None:
    canvas = Image.new("RGBA", (1920, 1080), COLORS["bg"])
    draw = ImageDraw.Draw(canvas)
    header(
        draw,
        "AWS/EKS Runtime Topology",
        "AWS 관리 영역과 Customer VPC의 실제 배치 경계를 구분",
        "TARGET · 기술 검토 View",
    )

    group(draw, (40, 200, 1870, 1015), "AWS Account · Test Environment", COLORS["orange"])
    group(draw, (320, 255, 1825, 965), "Region · ap-northeast-2", COLORS["teal"])

    node(draw, (45, 120, 235, 190), "사용자·Test Runner", COLORS["blue_light"], COLORS["blue"], 16)
    service_tile(
        canvas,
        draw,
        (70, 325, 210, 500),
        "route53",
        "Route 53",
        "Global DNS",
        COLORS["purple"],
    )
    arrow(draw, (140, 190), (140, 325), COLORS["blue"], 4)

    group(
        draw,
        (365, 315, 1450, 465),
        "AWS-managed EKS Control Plane · Customer VPC 밖",
        COLORS["orange"],
        COLORS["orange_light"],
        17,
    )
    paste_icon(canvas, "eks", (690, 390), 64)
    draw.text(
        (740, 390),
        "Kubernetes API · etcd · Control Plane",
        font=font(18, True),
        fill=COLORS["ink"],
        anchor="lm",
    )
    draw.text(
        (1225, 390),
        "AWS가 Multi-AZ로 운영",
        font=font(15),
        fill=COLORS["muted"],
        anchor="mm",
    )

    group(draw, (365, 510, 1450, 905), "Customer VPC", COLORS["purple"], COLORS["card"])

    group(
        draw,
        (410, 560, 1405, 680),
        "Public Subnets · ALB는 2개 이상의 AZ Subnet에 연결",
        COLORS["blue"],
        COLORS["blue_light"],
        16,
    )
    draw.text((445, 620), "AZ-a", font=font(15, True), fill=COLORS["blue"])
    draw.text((1325, 620), "AZ-c", font=font(15, True), fill=COLORS["blue"])
    paste_icon(canvas, "alb", (905, 615), 58)
    draw.text((905, 650), "Application Load Balancer", font=font(16, True), fill=COLORS["ink"], anchor="ma")

    group(
        draw,
        (410, 720, 865, 870),
        "Private App Subnet · AZ-a",
        COLORS["teal"],
        COLORS["teal_light"],
        16,
    )
    group(
        draw,
        (950, 720, 1405, 870),
        "Private App Subnet · AZ-c",
        COLORS["teal"],
        COLORS["teal_light"],
        16,
    )

    for x, label in [(455, "Worker Node A"), (995, "Worker Node C")]:
        node(draw, (x, 775, x + 160, 845), label, COLORS["card"], COLORS["teal"], 15)
        node(draw, (x + 185, 755, x + 365, 800), "Pod · vulnerable", COLORS["red_light"], COLORS["red"], 13)
        node(draw, (x + 185, 815, x + 365, 860), "Pod · remediated", COLORS["green_light"], COLORS["green"], 13)

    draw.text(
        (907, 892),
        "하나의 EKS Cluster Data Plane이 여러 AZ의 Node Group을 사용",
        font=font(16, True),
        fill=COLORS["teal"],
        anchor="mm",
    )

    service_tile(
        canvas,
        draw,
        (1510, 315, 1675, 490),
        "waf",
        "AWS WAF",
        "ALB에 연결",
        COLORS["red"],
    )
    service_tile(
        canvas,
        draw,
        (1510, 535, 1675, 710),
        "iam",
        "IAM",
        "Pod Identity / IRSA",
        COLORS["magenta"],
    )
    service_tile(
        canvas,
        draw,
        (1510, 755, 1675, 930),
        "s3",
        "Amazon S3",
        "보호 대상",
        COLORS["green"],
    )

    node(
        draw,
        (1245, 875, 1410, 900),
        "S3 Gateway Endpoint",
        COLORS["green_light"],
        COLORS["green"],
        12,
    )

    orthogonal_arrow(
        draw,
        [(210, 412), (275, 412), (275, 615), (875, 615)],
        COLORS["blue"],
        4,
    )
    draw.text((250, 390), "DNS → ALB Endpoint", font=font(13, True), fill=COLORS["blue"])
    dashed_line(draw, (1510, 402), (1475, 402), COLORS["red"], 4)
    dashed_line(draw, (1475, 402), (1475, 615), COLORS["red"], 4)
    dashed_line(draw, (1475, 615), (1405, 615), COLORS["red"], 4)
    draw.text((1470, 505), "Association", font=font(13, True), fill=COLORS["red"], anchor="mm")
    arrow(draw, (905, 680), (905, 720), COLORS["blue"], 4)

    dashed_line(draw, (535, 465), (535, 775), COLORS["purple"], 3)
    dashed_line(draw, (1075, 465), (1075, 775), COLORS["purple"], 3)
    draw.text((905, 490), "Control Plane ↕ Worker Nodes", font=font(13), fill=COLORS["purple"], anchor="mm")

    arrow(draw, (1360, 782), (1510, 622), COLORS["magenta"], 4, True)
    arrow(draw, (1320, 860), (1320, 875), COLORS["green"], 4)
    arrow(draw, (1410, 888), (1510, 842), COLORS["green"], 4)

    node(
        draw,
        (1705, 315, 1810, 475),
        "확장 후보\n\nCloudFront\nRDS · EFS\nDR Region",
        COLORS["gray_light"],
        COLORS["border"],
        14,
    )
    draw.text(
        (1758, 500),
        "요구 확정 전에는\n본 경로에 포함하지 않음",
        font=font(12),
        fill=COLORS["muted"],
        anchor="ma",
        align="center",
    )

    legend_item(draw, 420, 940, "Application Traffic", COLORS["blue"])
    legend_item(draw, 700, 940, "Control Plane", COLORS["purple"], True)
    legend_item(draw, 940, 940, "IAM 관계", COLORS["magenta"], True)
    legend_item(draw, 1160, 940, "Data Access", COLORS["green"])

    canvas.convert("RGB").save(path, quality=96)


def draw_cicd_png(path: Path) -> None:
    canvas = Image.new("RGBA", (1920, 1080), COLORS["bg"])
    draw = ImageDraw.Draw(canvas)
    header(
        draw,
        "DevSecOps Delivery & Security Verification",
        "Application 자동화와 Terraform 보호 단계를 분리하고, Runtime 증거로 다시 연결",
        "TARGET · 운영 흐름 View",
    )

    group(draw, (45, 150, 1875, 510), "Application Pipeline · 자동", COLORS["green"])

    stage_boxes = [
        ((80, 245, 270, 380), "1\nGit Push / PR", COLORS["gray_light"], COLORS["ink"]),
        ((320, 225, 560, 400), "2\nTest · SAST · SCA\nSecret Scan", COLORS["blue_light"], COLORS["blue"]),
        ((610, 245, 800, 380), "3\nContainer Build", COLORS["green_light"], COLORS["green"]),
        ((850, 245, 1040, 380), "4\nImage Scan", COLORS["purple_light"], COLORS["purple"]),
        ((1090, 225, 1270, 400), "", COLORS["card"], COLORS["orange"]),
        ((1320, 245, 1510, 380), "6\nTest Namespace\n자동 배포", COLORS["green_light"], COLORS["green"]),
        ((1560, 225, 1835, 400), "7\nSmoke Test\n통제된 공격·장애", COLORS["red_light"], COLORS["red"]),
    ]
    for box, label, fill, accent in stage_boxes:
        if label:
            node(draw, box, label, fill, accent, 17)
        else:
            rounded(draw, box, fill, accent, 2, 14)
            step_badge(draw, (1118, 252), 5, COLORS["orange"])
            paste_icon(canvas, "ecr", (1180, 300), 64)
            draw.text((1180, 350), "Amazon ECR", font=font(17, True), fill=COLORS["ink"], anchor="ma")

    for start, end in [
        ((270, 312), (320, 312)),
        ((560, 312), (610, 312)),
        ((800, 312), (850, 312)),
        ((1040, 312), (1090, 312)),
        ((1270, 312), (1320, 312)),
        ((1510, 312), (1560, 312)),
    ]:
        arrow(draw, start, end, COLORS["green"], 4)

    draw.text(
        (80, 445),
        "CI/CD Engine은 미확정 · GitHub Actions, GitLab CI, CodePipeline 등 실제 팀 선택에 맞춰 이름만 교체",
        font=font(15),
        fill=COLORS["muted"],
    )

    group(draw, (45, 545, 1875, 770), "Evidence Gate · 자동 수집 + 사람이 판정", COLORS["orange"])
    node(
        draw,
        (100, 615, 430, 705),
        "CloudWatch · CloudTrail · EKS Audit\nWAF·ALB·Application Log",
        COLORS["orange_light"],
        COLORS["orange"],
        15,
    )
    node(
        draw,
        (540, 615, 810, 705),
        "Before / After 비교\n탐지·차단·피해·재현성",
        COLORS["blue_light"],
        COLORS["blue"],
        16,
    )
    node(
        draw,
        (920, 615, 1130, 705),
        "Security Gate\n통과?",
        COLORS["purple_light"],
        COLORS["purple"],
        17,
    )
    node(
        draw,
        (1240, 585, 1480, 655),
        "PASS",
        COLORS["green_light"],
        COLORS["green"],
        17,
    )
    node(
        draw,
        (1240, 680, 1480, 750),
        "FAIL\nIssue · 조치 · 재실행",
        COLORS["red_light"],
        COLORS["red"],
        16,
    )
    node(
        draw,
        (1585, 585, 1810, 655),
        "결과 보고서\nRelease Candidate",
        COLORS["green_light"],
        COLORS["green"],
        16,
    )
    for start, end, color in [
        ((430, 660), (540, 660), COLORS["orange"]),
        ((810, 660), (920, 660), COLORS["orange"]),
        ((1130, 635), (1240, 620), COLORS["green"]),
        ((1130, 685), (1240, 715), COLORS["red"]),
        ((1480, 620), (1585, 620), COLORS["green"]),
    ]:
        arrow(draw, start, end, color, 4)
    draw.text((1175, 605), "Yes", font=font(13, True), fill=COLORS["green"], anchor="mm")
    draw.text((1175, 705), "No", font=font(13, True), fill=COLORS["red"], anchor="mm")
    orthogonal_arrow(
        draw,
        [(1360, 750), (1360, 780), (175, 780), (175, 400)],
        COLORS["red"],
        3,
    )
    orthogonal_arrow(
        draw,
        [(1695, 400), (1695, 525), (265, 525), (265, 615)],
        COLORS["orange"],
        3,
    )
    draw.text(
        (1480, 520),
        "Runtime Telemetry",
        font=font(13, True),
        fill=COLORS["orange"],
        anchor="mm",
    )

    group(draw, (45, 805, 1875, 1015), "Infrastructure Pipeline · Terraform · 보호된 변경", COLORS["purple"])
    infra = [
        ((90, 880, 305, 955), "Terraform 변경"),
        ((375, 865, 650, 970), "fmt · validate\nIaC Security Scan"),
        ((720, 880, 935, 955), "terraform plan"),
        ((1005, 865, 1275, 970), "보호된 승인\n비용·삭제·권한"),
        ((1345, 880, 1555, 955), "terraform apply"),
        ((1625, 865, 1830, 970), "AWS 실제 상태\n검증"),
    ]
    for idx, (box, label) in enumerate(infra):
        fill = COLORS["gray_light"]
        accent = COLORS["ink"]
        if idx in (1, 2):
            fill, accent = COLORS["purple_light"], COLORS["purple"]
        elif idx == 3:
            fill, accent = COLORS["orange_light"], COLORS["orange"]
        elif idx == 4:
            fill, accent = COLORS["green_light"], COLORS["green"]
        elif idx == 5:
            fill, accent = COLORS["blue_light"], COLORS["blue"]
        node(draw, box, label, fill, accent, 15)
    for start, end in [
        ((305, 918), (375, 918)),
        ((650, 918), (720, 918)),
        ((935, 918), (1005, 918)),
        ((1275, 918), (1345, 918)),
        ((1555, 918), (1625, 918)),
    ]:
        arrow(draw, start, end, COLORS["purple"], 4)

    draw.text(
        (960, 1040),
        "취약 Workload는 격리된 Test 환경에만 배포 · 실제 Secret·Access Key·kubeconfig는 Pipeline Artifact에 저장하지 않음",
        font=font(16, True),
        fill=COLORS["red"],
        anchor="mm",
    )

    canvas.convert("RGB").save(path, quality=96)


@dataclass
class DrawioCell:
    cell_id: str
    value: str
    style: str
    x: int
    y: int
    width: int
    height: int
    parent: str = "1"


def add_vertex(root: ET.Element, cell: DrawioCell) -> None:
    mx = ET.SubElement(
        root,
        "mxCell",
        {
            "id": cell.cell_id,
            "value": cell.value,
            "style": cell.style,
            "vertex": "1",
            "parent": cell.parent,
        },
    )
    ET.SubElement(
        mx,
        "mxGeometry",
        {
            "x": str(cell.x),
            "y": str(cell.y),
            "width": str(cell.width),
            "height": str(cell.height),
            "as": "geometry",
        },
    )


def add_edge(
    root: ET.Element,
    edge_id: str,
    source: str,
    target: str,
    color: str,
    dashed: bool = False,
    label: str = "",
) -> None:
    style = (
        "edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;"
        f"jettySize=auto;html=1;strokeWidth=3;strokeColor={color};"
        "endArrow=block;endFill=1;fontFamily=Malgun Gothic;fontSize=12;"
    )
    if dashed:
        style += "dashed=1;dashPattern=8 8;"
    cell = ET.SubElement(
        root,
        "mxCell",
        {
            "id": edge_id,
            "value": label,
            "style": style,
            "edge": "1",
            "parent": "1",
            "source": source,
            "target": target,
        },
    )
    ET.SubElement(cell, "mxGeometry", {"relative": "1", "as": "geometry"})


def icon_style(key: str) -> str:
    data = base64.b64encode(icon_file(key).read_bytes()).decode("ascii")
    return (
        "shape=label;image=data:image/png;base64,"
        + data
        + ";imageWidth=56;imageHeight=56;imageAlign=center;"
        "imageVerticalAlign=top;align=center;verticalAlign=bottom;"
        "fontFamily=Malgun Gothic;fontSize=14;fontStyle=1;whiteSpace=wrap;"
        "html=1;strokeColor=none;fillColor=none;"
    )


def box_style(fill: str, stroke: str, size: int = 14) -> str:
    return (
        f"rounded=1;whiteSpace=wrap;html=1;fillColor={fill};"
        f"strokeColor={stroke};strokeWidth=2;fontFamily=Malgun Gothic;"
        f"fontSize={size};fontStyle=1;align=center;verticalAlign=middle;"
    )


def group_style(fill: str, stroke: str, size: int = 16) -> str:
    return (
        f"rounded=1;whiteSpace=wrap;html=1;fillColor={fill};"
        f"strokeColor={stroke};strokeWidth=3;fontFamily=Malgun Gothic;"
        f"fontSize={size};fontStyle=1;align=left;verticalAlign=top;"
        "spacingTop=8;spacingLeft=8;"
    )


def text_style(size: int = 24) -> str:
    return (
        "text;html=1;align=left;verticalAlign=middle;"
        f"fontFamily=Malgun Gothic;fontSize={size};fontStyle=1;"
        "strokeColor=none;fillColor=none;"
    )


def make_page(name: str) -> tuple[ET.Element, ET.Element]:
    diagram = ET.Element("diagram", {"name": name, "id": name.replace(" ", "-")})
    model = ET.SubElement(
        diagram,
        "mxGraphModel",
        {
            "dx": "1422",
            "dy": "794",
            "grid": "1",
            "gridSize": "10",
            "guides": "1",
            "tooltips": "1",
            "connect": "1",
            "arrows": "1",
            "fold": "1",
            "page": "1",
            "pageScale": "1",
            "pageWidth": "1920",
            "pageHeight": "1080",
            "math": "0",
            "shadow": "0",
        },
    )
    root = ET.SubElement(model, "root")
    ET.SubElement(root, "mxCell", {"id": "0"})
    ET.SubElement(root, "mxCell", {"id": "1", "parent": "0"})
    return diagram, root


def executive_drawio_page() -> ET.Element:
    diagram, root = make_page("01 Executive Security")
    cells = [
        DrawioCell("title", "3차 프로젝트 · Security Architecture", text_style(28), 35, 20, 900, 55),
        DrawioCell("attack", "Attack Path · 무엇을 검증하는가", group_style("#FFFFFF", COLORS["red"]), 35, 100, 1810, 390),
        DrawioCell("actor", "1 · 통제된 공격 Runner<br>허용 IP · Test Window", box_style(COLORS["red_light"], COLORS["red"]), 80, 220, 220, 90),
        DrawioCell("edge", "2 · Route 53 · ALB<br>WAF Association", box_style(COLORS["purple_light"], COLORS["purple"]), 375, 210, 260, 110),
        DrawioCell("eks", "3 · EKS Test Workload<br>취약 Pod · ServiceAccount", icon_style("eks"), 720, 185, 220, 155),
        DrawioCell("iam", "4 · IAM Role<br>Pod Identity / IRSA 오구성", icon_style("iam"), 1025, 185, 220, 155),
        DrawioCell("s3", "5 · Amazon S3<br>민감 데이터 Target", icon_style("s3"), 1330, 185, 220, 155),
        DrawioCell("detect", "Detect → Remediate → Retest", group_style("#FFFFFF", COLORS["orange"]), 35, 530, 1810, 360),
        DrawioCell("logs", "Log Sources<br>WAF·ALB · EKS Audit<br>CloudTrail · VPC Flow", box_style(COLORS["orange_light"], COLORS["orange"]), 90, 650, 280, 110),
        DrawioCell("evidence", "CloudWatch · S3 Evidence<br>원본 증거 보존", box_style(COLORS["orange_light"], COLORS["orange"]), 465, 650, 260, 110),
        DrawioCell("compare", "Before / After<br>탐지·차단·피해·재현성", box_style(COLORS["blue_light"], COLORS["blue"]), 820, 650, 260, 110),
        DrawioCell("fix", "조치 버전 배포<br>IAM·Manifest·Image", box_style(COLORS["green_light"], COLORS["green"]), 1175, 650, 230, 110),
        DrawioCell("retest", "동일 조건 재실행<br>같은 입력·관찰 지점", box_style(COLORS["purple_light"], COLORS["purple"]), 1500, 650, 260, 110),
    ]
    for cell in cells:
        add_vertex(root, cell)
    for edge_id, source, target, color in [
        ("a1", "actor", "edge", COLORS["red"]),
        ("a2", "edge", "eks", COLORS["red"]),
        ("a3", "eks", "iam", COLORS["red"]),
        ("a4", "iam", "s3", COLORS["red"]),
        ("d1", "logs", "evidence", COLORS["orange"]),
        ("d2", "evidence", "compare", COLORS["orange"]),
        ("d3", "compare", "fix", COLORS["green"]),
        ("d4", "fix", "retest", COLORS["green"]),
    ]:
        add_edge(root, edge_id, source, target, color)
    return diagram


def runtime_drawio_page() -> ET.Element:
    diagram, root = make_page("02 Runtime Topology")
    cells = [
        DrawioCell("title", "AWS/EKS Runtime Topology", text_style(28), 35, 20, 850, 55),
        DrawioCell("account", "AWS Account · Test Environment", group_style("#FFFFFF", COLORS["orange"]), 20, 180, 1820, 800),
        DrawioCell("region", "Region · ap-northeast-2", group_style("#FFFFFF", COLORS["teal"]), 255, 235, 1540, 700),
        DrawioCell("actor", "사용자 · Test Runner", box_style(COLORS["blue_light"], COLORS["blue"]), 25, 90, 150, 65),
        DrawioCell("route53", "Route 53<br>Global DNS", icon_style("route53"), 50, 280, 120, 120),
        DrawioCell("control", "AWS-managed EKS Control Plane<br>Customer VPC 밖 · AWS가 Multi-AZ 운영", box_style(COLORS["orange_light"], COLORS["orange"]), 350, 300, 890, 90),
        DrawioCell("vpc", "Customer VPC", group_style("#FFFFFF", COLORS["purple"]), 350, 440, 1050, 430),
        DrawioCell("public", "Public Subnets · ALB는 2개 이상의 AZ Subnet에 연결", group_style(COLORS["blue_light"], COLORS["blue"], 14), 395, 500, 960, 105),
        DrawioCell("alb", "Application Load Balancer", icon_style("alb"), 805, 505, 140, 90),
        DrawioCell("aza", "Private App Subnet · AZ-a", group_style(COLORS["teal_light"], COLORS["teal"], 14), 395, 650, 420, 165),
        DrawioCell("azc", "Private App Subnet · AZ-c", group_style(COLORS["teal_light"], COLORS["teal"], 14), 935, 650, 420, 165),
        DrawioCell("nodea", "Worker Node A<br>Pod · vulnerable / remediated", box_style("#FFFFFF", COLORS["teal"]), 440, 715, 320, 70),
        DrawioCell("nodec", "Worker Node C<br>Pod · vulnerable / remediated", box_style("#FFFFFF", COLORS["teal"]), 980, 715, 320, 70),
        DrawioCell("waf", "AWS WAF<br>ALB Association", icon_style("waf"), 1470, 300, 150, 130),
        DrawioCell("iam", "IAM<br>Pod Identity / IRSA", icon_style("iam"), 1470, 500, 150, 130),
        DrawioCell("s3", "Amazon S3<br>보호 대상", icon_style("s3"), 1470, 700, 150, 130),
        DrawioCell("future", "확장 후보 · 미확정<br>CloudFront · RDS · EFS · DR Region", box_style(COLORS["gray_light"], COLORS["border"]), 1650, 300, 130, 190),
    ]
    for cell in cells:
        add_vertex(root, cell)
    edges = [
        ("r1", "actor", "route53", COLORS["blue"], False, ""),
        ("r2", "route53", "alb", COLORS["blue"], False, "DNS → Endpoint"),
        ("r3", "control", "nodea", COLORS["purple"], True, "Control Plane"),
        ("r4", "control", "nodec", COLORS["purple"], True, "Control Plane"),
        ("r5", "waf", "alb", COLORS["red"], True, "Association"),
        ("r6", "nodec", "iam", COLORS["magenta"], True, "Role"),
        ("r7", "nodec", "s3", COLORS["green"], False, "Data Access"),
    ]
    for edge in edges:
        add_edge(root, *edge)
    return diagram


def cicd_drawio_page() -> ET.Element:
    diagram, root = make_page("03 DevSecOps Verification")
    cells = [
        DrawioCell("title", "DevSecOps Delivery & Security Verification", text_style(28), 35, 20, 1100, 55),
        DrawioCell("app", "Application Pipeline · 자동", group_style("#FFFFFF", COLORS["green"]), 35, 100, 1810, 330),
        DrawioCell("git", "1 · Git Push / PR", box_style(COLORS["gray_light"], COLORS["ink"]), 75, 220, 170, 70),
        DrawioCell("checks", "2 · Test · SAST · SCA<br>Secret Scan", box_style(COLORS["blue_light"], COLORS["blue"]), 300, 205, 230, 100),
        DrawioCell("build", "3 · Container Build", box_style(COLORS["green_light"], COLORS["green"]), 585, 220, 180, 70),
        DrawioCell("scan", "4 · Image Scan", box_style(COLORS["purple_light"], COLORS["purple"]), 820, 220, 180, 70),
        DrawioCell("ecr", "5 · Amazon ECR", icon_style("ecr"), 1055, 185, 140, 140),
        DrawioCell("deploy", "6 · Test Namespace<br>자동 배포", box_style(COLORS["green_light"], COLORS["green"]), 1250, 205, 190, 100),
        DrawioCell("test", "7 · Smoke Test<br>통제된 공격·장애", box_style(COLORS["red_light"], COLORS["red"]), 1495, 205, 250, 100),
        DrawioCell("gate", "Evidence Gate · 자동 수집 + 사람이 판정", group_style("#FFFFFF", COLORS["orange"]), 35, 470, 1810, 250),
        DrawioCell("logs", "CloudWatch · CloudTrail · EKS Audit<br>WAF·ALB·Application Log", box_style(COLORS["orange_light"], COLORS["orange"]), 100, 565, 340, 90),
        DrawioCell("compare", "Before / After<br>탐지·차단·피해·재현성", box_style(COLORS["blue_light"], COLORS["blue"]), 540, 565, 280, 90),
        DrawioCell("decision", "Security Gate<br>통과?", box_style(COLORS["purple_light"], COLORS["purple"]), 920, 565, 200, 90),
        DrawioCell("pass", "PASS", box_style(COLORS["green_light"], COLORS["green"]), 1220, 535, 210, 65),
        DrawioCell("fail", "FAIL<br>Issue · 조치 · 재실행", box_style(COLORS["red_light"], COLORS["red"]), 1220, 625, 210, 65),
        DrawioCell("report", "결과 보고서<br>Release Candidate", box_style(COLORS["green_light"], COLORS["green"]), 1530, 535, 230, 65),
        DrawioCell("infra", "Infrastructure Pipeline · Terraform · 보호된 변경", group_style("#FFFFFF", COLORS["purple"]), 35, 760, 1810, 250),
        DrawioCell("tf", "Terraform 변경", box_style(COLORS["gray_light"], COLORS["ink"]), 80, 865, 180, 70),
        DrawioCell("validate", "fmt · validate<br>IaC Security Scan", box_style(COLORS["purple_light"], COLORS["purple"]), 325, 850, 240, 100),
        DrawioCell("plan", "terraform plan", box_style(COLORS["purple_light"], COLORS["purple"]), 630, 865, 180, 70),
        DrawioCell("approval", "보호된 승인<br>비용·삭제·권한", box_style(COLORS["orange_light"], COLORS["orange"]), 875, 850, 230, 100),
        DrawioCell("apply", "terraform apply", box_style(COLORS["green_light"], COLORS["green"]), 1170, 865, 180, 70),
        DrawioCell("verify", "AWS 실제 상태<br>Runtime·비용·Security", box_style(COLORS["blue_light"], COLORS["blue"]), 1415, 850, 270, 100),
    ]
    for cell in cells:
        add_vertex(root, cell)
    for edge_id, source, target, color in [
        ("p1", "git", "checks", COLORS["green"]),
        ("p2", "checks", "build", COLORS["green"]),
        ("p3", "build", "scan", COLORS["green"]),
        ("p4", "scan", "ecr", COLORS["green"]),
        ("p5", "ecr", "deploy", COLORS["green"]),
        ("p6", "deploy", "test", COLORS["green"]),
        ("g1", "logs", "compare", COLORS["orange"]),
        ("g2", "compare", "decision", COLORS["orange"]),
        ("g3", "decision", "pass", COLORS["green"]),
        ("g4", "decision", "fail", COLORS["red"]),
        ("g5", "pass", "report", COLORS["green"]),
        ("i1", "tf", "validate", COLORS["purple"]),
        ("i2", "validate", "plan", COLORS["purple"]),
        ("i3", "plan", "approval", COLORS["purple"]),
        ("i4", "approval", "apply", COLORS["purple"]),
        ("i5", "apply", "verify", COLORS["purple"]),
    ]:
        add_edge(root, edge_id, source, target, color)
    add_edge(root, "telemetry", "test", "logs", COLORS["orange"], False, "Runtime Telemetry")
    add_edge(root, "feedback", "fail", "git", COLORS["red"], False, "조치 후 재실행")
    return diagram


def write_drawio(path: Path) -> None:
    mxfile = ET.Element(
        "mxfile",
        {
            "host": "app.diagrams.net",
            "modified": "2026-07-29T00:00:00.000Z",
            "agent": "Codex",
            "version": "24.7.17",
            "type": "device",
        },
    )
    mxfile.append(executive_drawio_page())
    mxfile.append(runtime_drawio_page())
    mxfile.append(cicd_drawio_page())
    ET.indent(mxfile, space="  ")
    path.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        + ET.tostring(mxfile, encoding="unicode"),
        encoding="utf-8",
        newline="\n",
    )


def main() -> None:
    ensure_icon_package()
    missing = [str(icon_file(key)) for key in ICON_PATHS if not icon_file(key).exists()]
    if missing:
        raise FileNotFoundError(
            "AWS icon package is missing required files.\n"
            f"Download: {AWS_ICON_PACKAGE}\n"
            + "\n".join(missing)
        )

    executive_png = OUTPUT_DIR / "3차프로젝트_AWS_Executive_Security_Architecture.png"
    runtime_png = OUTPUT_DIR / "3차프로젝트_AWS_Runtime_Target_Architecture.png"
    cicd_png = OUTPUT_DIR / "3차프로젝트_CICD_Security_Verification_Loop.png"
    drawio = OUTPUT_DIR / "3차프로젝트_AWS_Target_Architecture.drawio"

    draw_executive_png(executive_png)
    draw_runtime_png(runtime_png)
    draw_cicd_png(cicd_png)
    write_drawio(drawio)

    print(executive_png)
    print(runtime_png)
    print(cicd_png)
    print(drawio)


if __name__ == "__main__":
    main()
