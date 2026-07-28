from __future__ import annotations

import base64
import html
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
    "ink": "#232F3E",
    "muted": "#5F6B7A",
    "blue": "#147EBA",
    "blue_light": "#EAF5FB",
    "red": "#D13212",
    "red_light": "#FFF0ED",
    "green": "#1D8102",
    "green_light": "#ECF7E8",
    "orange": "#FF9900",
    "orange_light": "#FFF4E5",
    "purple": "#8B5CF6",
    "purple_light": "#F4F0FF",
    "gray": "#D5DBDB",
    "gray_light": "#F7F8F8",
    "white": "#FFFFFF",
    "aws_cloud": "#8C4FFF",
    "region": "#00A4A6",
    "vpc": "#8C4FFF",
    "public": "#2E73B8",
    "private": "#00A4A6",
    "data": "#3F8624",
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


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_BOLD if bold else FONT_REGULAR), size)


def text_bbox(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont):
    return draw.multiline_textbbox((0, 0), text, font=font, spacing=4, align="center")


def center_text(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: str = COLORS["ink"],
    spacing: int = 4,
):
    x1, y1, x2, y2 = box
    bbox = draw.multiline_textbbox(
        (0, 0), text, font=font, spacing=spacing, align="center"
    )
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]
    draw.multiline_text(
        ((x1 + x2 - width) / 2, (y1 + y2 - height) / 2),
        text,
        font=font,
        fill=fill,
        spacing=spacing,
        align="center",
    )


def rounded_box(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    fill: str,
    outline: str,
    width: int = 3,
    radius: int = 18,
):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def dashed_rectangle(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    outline: str,
    width: int = 3,
    dash: int = 12,
    gap: int = 8,
):
    x1, y1, x2, y2 = box
    for x in range(x1, x2, dash + gap):
        draw.line((x, y1, min(x + dash, x2), y1), fill=outline, width=width)
        draw.line((x, y2, min(x + dash, x2), y2), fill=outline, width=width)
    for y in range(y1, y2, dash + gap):
        draw.line((x1, y, x1, min(y + dash, y2)), fill=outline, width=width)
        draw.line((x2, y, x2, min(y + dash, y2)), fill=outline, width=width)


def arrow(
    draw: ImageDraw.ImageDraw,
    start: tuple[int, int],
    end: tuple[int, int],
    color: str,
    width: int = 5,
    dashed: bool = False,
):
    if dashed:
        sx, sy = start
        ex, ey = end
        distance = math.dist(start, end)
        if distance == 0:
            return
        ux = (ex - sx) / distance
        uy = (ey - sy) / distance
        pos = 0
        while pos < distance - 18:
            seg_end = min(pos + 16, distance - 18)
            draw.line(
                (
                    sx + ux * pos,
                    sy + uy * pos,
                    sx + ux * seg_end,
                    sy + uy * seg_end,
                ),
                fill=color,
                width=width,
            )
            pos += 27
    else:
        draw.line((*start, *end), fill=color, width=width)

    angle = math.atan2(end[1] - start[1], end[0] - start[0])
    size = 18
    p1 = (
        end[0] - size * math.cos(angle - math.pi / 6),
        end[1] - size * math.sin(angle - math.pi / 6),
    )
    p2 = (
        end[0] - size * math.cos(angle + math.pi / 6),
        end[1] - size * math.sin(angle + math.pi / 6),
    )
    draw.polygon((end, p1, p2), fill=color)


def service(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    key: str,
    center: tuple[int, int],
    label: str,
    icon_size: int = 72,
    font_size: int = 24,
):
    icon = Image.open(icon_file(key)).convert("RGBA")
    icon = icon.resize((icon_size, icon_size), Image.Resampling.LANCZOS)
    x = center[0] - icon_size // 2
    y = center[1] - icon_size // 2 - 16
    canvas.alpha_composite(icon, (x, y))
    draw.multiline_text(
        (center[0], y + icon_size + 6),
        label,
        font=load_font(font_size, bold=True),
        fill=COLORS["ink"],
        anchor="ma",
        align="center",
        spacing=3,
    )


def generic_node(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    label: str,
    fill: str,
    outline: str,
    font_size: int = 24,
):
    rounded_box(draw, box, fill, outline, width=3, radius=16)
    center_text(draw, box, label, load_font(font_size, bold=True))


def draw_runtime_png(path: Path):
    width, height = 2500, 1550
    canvas = Image.new("RGBA", (width, height), COLORS["white"])
    draw = ImageDraw.Draw(canvas)

    draw.text(
        (80, 45),
        "3차 프로젝트 AWS/EKS Target Architecture",
        font=load_font(42, bold=True),
        fill=COLORS["ink"],
    )
    draw.text(
        (82, 102),
        "제안 구조 · 실제 Terraform 및 Runtime 검증 전 · 2026-07-28",
        font=load_font(22),
        fill=COLORS["muted"],
    )

    # External actors
    generic_node(
        draw,
        (45, 270, 255, 365),
        "정상 사용자",
        COLORS["blue_light"],
        COLORS["blue"],
    )
    generic_node(
        draw,
        (45, 420, 255, 545),
        "통제된 공격 Runner\n허용 IP·Test Window",
        COLORS["red_light"],
        COLORS["red"],
        font_size=21,
    )

    # AWS Cloud / Region / VPC boundaries
    rounded_box(draw, (300, 175, 2440, 1440), "#FCFCFD", COLORS["aws_cloud"], 4, 22)
    draw.text(
        (330, 195),
        "AWS Cloud",
        font=load_font(28, bold=True),
        fill=COLORS["aws_cloud"],
    )

    rounded_box(draw, (560, 390, 1980, 1080), "#FFFFFF", COLORS["region"], 4, 20)
    draw.text(
        (590, 410),
        "Region: ap-northeast-2",
        font=load_font(25, bold=True),
        fill=COLORS["region"],
    )

    rounded_box(draw, (640, 480, 1900, 1015), "#FBF8FF", COLORS["vpc"], 4, 18)
    draw.text(
        (670, 498),
        "VPC",
        font=load_font(24, bold=True),
        fill=COLORS["vpc"],
    )

    # Subnets
    rounded_box(draw, (700, 555, 1840, 680), "#F0F7FF", COLORS["public"], 3, 14)
    draw.text(
        (720, 565),
        "Public Subnets · Multi-AZ",
        font=load_font(20, bold=True),
        fill=COLORS["public"],
    )

    rounded_box(draw, (700, 715, 1390, 955), "#EAF9F7", COLORS["private"], 3, 14)
    draw.text(
        (720, 725),
        "Private App Subnets · Multi-AZ",
        font=load_font(20, bold=True),
        fill=COLORS["private"],
    )

    rounded_box(draw, (1430, 715, 1840, 955), "#F1F8ED", COLORS["data"], 3, 14)
    draw.text(
        (1450, 725),
        "Data Subnets · Optional",
        font=load_font(20, bold=True),
        fill=COLORS["data"],
    )

    # Global traffic services
    service(canvas, draw, "route53", (400, 295), "Route 53\n(Optional)")
    service(canvas, draw, "cloudfront", (620, 295), "CloudFront\n(Optional)")
    service(canvas, draw, "waf", (840, 295), "AWS WAF")
    service(canvas, draw, "alb", (920, 620), "ALB")

    # Runtime
    service(canvas, draw, "eks", (925, 815), "Amazon EKS")
    generic_node(
        draw,
        (1035, 770, 1225, 835),
        "Ingress / Service",
        COLORS["blue_light"],
        COLORS["blue"],
        font_size=20,
    )
    generic_node(
        draw,
        (1035, 855, 1225, 930),
        "취약 → 조치\nWorkload",
        COLORS["red_light"],
        COLORS["red"],
        font_size=20,
    )

    service(canvas, draw, "rds", (1535, 820), "Amazon RDS\n(Optional)")
    service(canvas, draw, "efs", (1725, 820), "Amazon EFS\n(Optional)")

    # Delivery
    service(canvas, draw, "ecr", (510, 1195), "Amazon ECR")
    generic_node(
        draw,
        (700, 1150, 955, 1245),
        "자동 CD\nImage·Manifest 배포",
        COLORS["green_light"],
        COLORS["green"],
        font_size=22,
    )

    # Evidence plane
    dashed_rectangle(draw, (2015, 330, 2380, 1090), COLORS["orange"], 4)
    draw.text(
        (2040, 350),
        "Security & Evidence",
        font=load_font(24, bold=True),
        fill=COLORS["orange"],
    )
    service(canvas, draw, "cloudwatch", (2110, 485), "CloudWatch")
    service(canvas, draw, "cloudtrail", (2275, 485), "CloudTrail")
    service(canvas, draw, "guardduty", (2110, 700), "GuardDuty")
    service(canvas, draw, "s3", (2275, 700), "S3 Evidence")
    service(canvas, draw, "iam", (2110, 915), "IAM")
    generic_node(
        draw,
        (2180, 865, 2350, 970),
        "EKS·WAF·ALB\nApplication Log",
        COLORS["orange_light"],
        COLORS["orange"],
        font_size=19,
    )

    # Traffic arrows
    arrow(draw, (255, 317), (350, 317), COLORS["blue"])
    arrow(draw, (255, 482), (350, 335), COLORS["red"])
    arrow(draw, (450, 295), (570, 295), COLORS["blue"])
    arrow(draw, (670, 295), (790, 295), COLORS["blue"])
    arrow(draw, (840, 350), (900, 565), COLORS["blue"])
    arrow(draw, (920, 680), (925, 750), COLORS["blue"])
    arrow(draw, (970, 815), (1035, 803), COLORS["blue"])
    arrow(draw, (1130, 835), (1130, 855), COLORS["blue"])

    # Data connections
    arrow(draw, (1225, 892), (1490, 835), COLORS["purple"])
    arrow(draw, (1225, 905), (1680, 835), COLORS["purple"])

    # Delivery arrows
    arrow(draw, (565, 1195), (700, 1195), COLORS["green"])
    arrow(draw, (955, 1195), (1065, 930), COLORS["green"])

    # Evidence arrows
    arrow(draw, (840, 325), (2040, 455), COLORS["orange"], dashed=True)
    arrow(draw, (980, 620), (2040, 480), COLORS["orange"], dashed=True)
    arrow(draw, (1225, 890), (2040, 880), COLORS["orange"], dashed=True)
    arrow(draw, (1900, 520), (2040, 640), COLORS["orange"], dashed=True)

    # Legend
    legend_y = 1355
    draw.text(
        (395, legend_y),
        "Legend",
        font=load_font(22, bold=True),
        fill=COLORS["ink"],
    )
    legend_items = [
        ("정상 Traffic", COLORS["blue"], False),
        ("통제된 공격", COLORS["red"], False),
        ("CI/CD 배포", COLORS["green"], False),
        ("Log·Evidence", COLORS["orange"], True),
        ("Data·권한 관계", COLORS["purple"], False),
    ]
    x = 520
    for label, color, dashed in legend_items:
        arrow(draw, (x, legend_y + 15), (x + 70, legend_y + 15), color, 4, dashed)
        draw.text(
            (x + 82, legend_y + 15),
            label,
            font=load_font(18),
            fill=COLORS["ink"],
            anchor="lm",
        )
        x += 340

    canvas.convert("RGB").save(path, quality=96, dpi=(180, 180))


def draw_cicd_png(path: Path):
    width, height = 2500, 1320
    canvas = Image.new("RGBA", (width, height), COLORS["white"])
    draw = ImageDraw.Draw(canvas)

    draw.text(
        (80, 45),
        "3차 프로젝트 CI/CD & Security Verification Loop",
        font=load_font(42, bold=True),
        fill=COLORS["ink"],
    )
    draw.text(
        (82, 102),
        "Application Pipeline은 자동화 · Infrastructure 변경은 보호된 승인 단계",
        font=load_font(22),
        fill=COLORS["muted"],
    )

    # Application pipeline lane
    rounded_box(draw, (55, 175, 2445, 760), "#FCFCFD", COLORS["green"], 4, 22)
    draw.text(
        (85, 195),
        "Application CI/CD · 자동",
        font=load_font(27, bold=True),
        fill=COLORS["green"],
    )

    stages = [
        ((90, 305, 310, 410), "Git Push / PR", COLORS["gray_light"], COLORS["ink"]),
        ((380, 305, 650, 410), "Test\nSAST·SCA·Secret Scan", COLORS["blue_light"], COLORS["blue"]),
        ((720, 305, 940, 410), "Container Build", COLORS["green_light"], COLORS["green"]),
        ((1010, 305, 1230, 410), "Image Scan", COLORS["purple_light"], COLORS["purple"]),
        ((1510, 305, 1680, 410), "자동 CD", COLORS["green_light"], COLORS["green"]),
        ((1870, 305, 2050, 410), "Smoke Test", COLORS["blue_light"], COLORS["blue"]),
        ((2110, 305, 2390, 410), "통제된 공격·장애", COLORS["red_light"], COLORS["red"]),
    ]
    for box, label, fill, outline in stages:
        generic_node(draw, box, label, fill, outline, font_size=21)

    service(canvas, draw, "ecr", (1385, 355), "Amazon ECR", icon_size=68, font_size=20)
    service(canvas, draw, "eks", (1775, 355), "EKS Test Namespace", icon_size=68, font_size=18)
    service(canvas, draw, "cloudwatch", (2050, 570), "CloudWatch", icon_size=64, font_size=19)
    service(canvas, draw, "s3", (2250, 570), "S3 Evidence", icon_size=64, font_size=19)

    app_arrows = [
        ((310, 357), (380, 357)),
        ((650, 357), (720, 357)),
        ((940, 357), (1010, 357)),
        ((1230, 357), (1335, 357)),
        ((1435, 357), (1510, 357)),
        ((1680, 357), (1740, 357)),
        ((1810, 357), (1870, 357)),
        ((2050, 357), (2110, 357)),
    ]
    for start, end in app_arrows:
        arrow(draw, start, end, COLORS["green"])

    arrow(draw, (2265, 410), (2050, 515), COLORS["orange"], dashed=True)
    arrow(draw, (2265, 410), (2250, 515), COLORS["orange"], dashed=True)

    # Result and feedback loop
    generic_node(
        draw,
        (950, 565, 1290, 675),
        "Before / After 비교\n탐지·차단·피해·재현성",
        COLORS["orange_light"],
        COLORS["orange"],
        font_size=22,
    )
    arrow(draw, (2050, 620), (1290, 620), COLORS["orange"], dashed=True)
    arrow(draw, (2250, 620), (1290, 650), COLORS["orange"], dashed=True)
    arrow(draw, (950, 620), (250, 500), COLORS["red"])
    draw.text(
        (520, 585),
        "조치 후 같은 조건으로 재실행",
        font=load_font(21, bold=True),
        fill=COLORS["red"],
        anchor="mm",
    )

    # Infrastructure lane
    rounded_box(draw, (55, 805, 2445, 1225), "#FBF8FF", COLORS["purple"], 4, 22)
    draw.text(
        (85, 825),
        "Infrastructure Pipeline · Terraform",
        font=load_font(27, bold=True),
        fill=COLORS["purple"],
    )

    infra = [
        ((120, 945, 390, 1055), "Terraform 변경", COLORS["gray_light"], COLORS["ink"]),
        ((470, 945, 790, 1055), "fmt · validate\nIaC Security Scan", COLORS["blue_light"], COLORS["blue"]),
        ((870, 945, 1130, 1055), "terraform plan", COLORS["purple_light"], COLORS["purple"]),
        ((1210, 925, 1515, 1075), "보호된 승인 단계\n비용·삭제·권한 검토", COLORS["orange_light"], COLORS["orange"]),
        ((1595, 945, 1865, 1055), "terraform apply", COLORS["green_light"], COLORS["green"]),
        ((1945, 925, 2350, 1075), "AWS 실제 상태 확인\nRuntime·비용·Security", COLORS["blue_light"], COLORS["blue"]),
    ]
    for box, label, fill, outline in infra:
        generic_node(draw, box, label, fill, outline, font_size=22)
    for start, end in [
        ((390, 1000), (470, 1000)),
        ((790, 1000), (870, 1000)),
        ((1130, 1000), (1210, 1000)),
        ((1515, 1000), (1595, 1000)),
        ((1865, 1000), (1945, 1000)),
    ]:
        arrow(draw, start, end, COLORS["purple"])

    draw.text(
        (1250, 1270),
        "취약 Workload는 격리된 Test 환경에서만 배포하고, 실제 Secret·Access Key·kubeconfig는 Pipeline Artifact에 남기지 않는다.",
        font=load_font(20, bold=True),
        fill=COLORS["red"],
        anchor="mm",
    )

    canvas.convert("RGB").save(path, quality=96, dpi=(180, 180))


def png_data_uri(path: Path) -> str:
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode("ascii")


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


def add_vertex(root: ET.Element, cell: DrawioCell):
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
):
    style = (
        f"edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;"
        f"jettySize=auto;html=1;strokeWidth=3;strokeColor={color};"
        f"endArrow=block;endFill=1;"
    )
    if dashed:
        style += "dashed=1;dashPattern=8 8;"
    mx = ET.SubElement(
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
    ET.SubElement(mx, "mxGeometry", {"relative": "1", "as": "geometry"})


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


def box_style(fill: str, stroke: str, font_size: int = 14) -> str:
    return (
        f"rounded=1;whiteSpace=wrap;html=1;fillColor={fill};"
        f"strokeColor={stroke};strokeWidth=2;fontFamily=Malgun Gothic;"
        f"fontSize={font_size};fontStyle=1;align=center;verticalAlign=middle;"
    )


def group_style(fill: str, stroke: str, dashed: bool = False) -> str:
    style = (
        f"rounded=1;whiteSpace=wrap;html=1;fillColor={fill};"
        f"strokeColor={stroke};strokeWidth=3;fontFamily=Malgun Gothic;"
        "fontSize=16;fontStyle=1;align=left;verticalAlign=top;"
        "spacingTop=8;spacingLeft=8;"
    )
    if dashed:
        style += "dashed=1;dashPattern=8 8;"
    return style


def make_page(name: str, page_width: int, page_height: int):
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
            "pageWidth": str(page_width),
            "pageHeight": str(page_height),
            "math": "0",
            "shadow": "0",
        },
    )
    root = ET.SubElement(model, "root")
    ET.SubElement(root, "mxCell", {"id": "0"})
    ET.SubElement(root, "mxCell", {"id": "1", "parent": "0"})
    return diagram, root


def runtime_drawio_page():
    diagram, root = make_page("Runtime & Security", 1700, 1100)

    cells = [
        DrawioCell(
            "title",
            "3차 프로젝트 AWS/EKS Target Architecture<br><font style='font-size:12px'>제안 구조 · 실제 Terraform 및 Runtime 검증 전</font>",
            "text;html=1;align=left;verticalAlign=middle;fontFamily=Malgun Gothic;fontSize=24;fontStyle=1;strokeColor=none;fillColor=none;",
            20,
            10,
            950,
            55,
        ),
        DrawioCell("aws", "AWS Cloud", group_style("#FCFCFD", COLORS["aws_cloud"]), 160, 85, 1490, 940),
        DrawioCell("region", "Region: ap-northeast-2", group_style("#FFFFFF", COLORS["region"]), 340, 245, 980, 520),
        DrawioCell("vpc", "VPC", group_style("#FBF8FF", COLORS["vpc"]), 420, 320, 820, 390),
        DrawioCell("pub", "Public Subnets · Multi-AZ", group_style("#F0F7FF", COLORS["public"]), 460, 380, 740, 95),
        DrawioCell("private", "Private App Subnets · Multi-AZ", group_style("#EAF9F7", COLORS["private"]), 460, 500, 470, 165),
        DrawioCell("data", "Data Subnets · Optional", group_style("#F1F8ED", COLORS["data"]), 960, 500, 240, 165),
        DrawioCell("evidence", "Security & Evidence", group_style("#FFFDF8", COLORS["orange"], True), 1360, 220, 250, 545),
        DrawioCell("user", "정상 사용자", box_style(COLORS["blue_light"], COLORS["blue"]), 20, 170, 120, 60),
        DrawioCell("tester", "통제된 공격 Runner<br>허용 IP·Test Window", box_style(COLORS["red_light"], COLORS["red"], 12), 20, 270, 120, 80),
        DrawioCell("route53", "Route 53<br>(Optional)", icon_style("route53"), 195, 150, 100, 105),
        DrawioCell("cloudfront", "CloudFront<br>(Optional)", icon_style("cloudfront"), 340, 150, 100, 105),
        DrawioCell("waf", "AWS WAF", icon_style("waf"), 485, 150, 100, 105),
        DrawioCell("alb", "ALB", icon_style("alb"), 560, 380, 100, 90),
        DrawioCell("eks", "Amazon EKS", icon_style("eks"), 520, 525, 110, 110),
        DrawioCell("ingress", "Ingress / Service", box_style(COLORS["blue_light"], COLORS["blue"], 12), 650, 525, 120, 50),
        DrawioCell("workload", "취약 → 조치<br>Workload", box_style(COLORS["red_light"], COLORS["red"], 12), 650, 595, 120, 55),
        DrawioCell("rds", "Amazon RDS<br>(Optional)", icon_style("rds"), 975, 535, 100, 110),
        DrawioCell("efs", "Amazon EFS<br>(Optional)", icon_style("efs"), 1085, 535, 100, 110),
        DrawioCell("ecr", "Amazon ECR", icon_style("ecr"), 250, 815, 100, 110),
        DrawioCell("cd", "자동 CD<br>Image·Manifest 배포", box_style(COLORS["green_light"], COLORS["green"], 12), 395, 840, 160, 65),
        DrawioCell("cw", "CloudWatch", icon_style("cloudwatch"), 1385, 290, 95, 105),
        DrawioCell("ct", "CloudTrail", icon_style("cloudtrail"), 1495, 290, 95, 105),
        DrawioCell("gd", "GuardDuty", icon_style("guardduty"), 1385, 445, 95, 105),
        DrawioCell("s3", "S3 Evidence", icon_style("s3"), 1495, 445, 95, 105),
        DrawioCell("iam", "IAM", icon_style("iam"), 1385, 600, 95, 105),
        DrawioCell("logs", "EKS·WAF·ALB<br>Application Log", box_style(COLORS["orange_light"], COLORS["orange"], 11), 1490, 615, 100, 65),
        DrawioCell(
            "legend",
            "<font color='#147EBA'>━ 정상 Traffic</font>　"
            "<font color='#D13212'>━ 통제된 공격</font>　"
            "<font color='#1D8102'>━ CI/CD</font>　"
            "<font color='#FF9900'>┅ Log·Evidence</font>　"
            "<font color='#8B5CF6'>━ Data·권한</font>",
            "text;html=1;align=center;verticalAlign=middle;fontFamily=Malgun Gothic;fontSize=13;fontStyle=1;strokeColor=#D5DBDB;fillColor=#FFFFFF;rounded=1;",
            330,
            950,
            1000,
            45,
        ),
    ]
    for cell in cells:
        add_vertex(root, cell)

    edges = [
        ("e1", "user", "route53", COLORS["blue"], False, ""),
        ("e2", "tester", "route53", COLORS["red"], False, ""),
        ("e3", "route53", "cloudfront", COLORS["blue"], False, ""),
        ("e4", "cloudfront", "waf", COLORS["blue"], False, ""),
        ("e5", "waf", "alb", COLORS["blue"], False, ""),
        ("e6", "alb", "eks", COLORS["blue"], False, ""),
        ("e7", "eks", "ingress", COLORS["blue"], False, ""),
        ("e8", "ingress", "workload", COLORS["blue"], False, ""),
        ("e9", "workload", "rds", COLORS["purple"], False, ""),
        ("e10", "workload", "efs", COLORS["purple"], False, ""),
        ("e11", "ecr", "cd", COLORS["green"], False, ""),
        ("e12", "cd", "workload", COLORS["green"], False, ""),
        ("e13", "waf", "cw", COLORS["orange"], True, ""),
        ("e14", "alb", "cw", COLORS["orange"], True, ""),
        ("e15", "workload", "logs", COLORS["orange"], True, ""),
        ("e16", "logs", "cw", COLORS["orange"], True, ""),
        ("e17", "ct", "gd", COLORS["orange"], True, ""),
        ("e18", "cw", "s3", COLORS["orange"], True, ""),
        ("e19", "iam", "workload", COLORS["purple"], True, ""),
    ]
    for edge in edges:
        add_edge(root, *edge)
    return diagram


def cicd_drawio_page():
    diagram, root = make_page("CI-CD & Verification", 1700, 900)

    cells = [
        DrawioCell(
            "title",
            "3차 프로젝트 CI/CD & Security Verification Loop<br><font style='font-size:12px'>Application 자동화 · Infrastructure 보호된 승인 단계</font>",
            "text;html=1;align=left;verticalAlign=middle;fontFamily=Malgun Gothic;fontSize=24;fontStyle=1;strokeColor=none;fillColor=none;",
            20,
            10,
            1000,
            55,
        ),
        DrawioCell("app_lane", "Application CI/CD · 자동", group_style("#FCFCFD", COLORS["green"]), 25, 90, 1630, 390),
        DrawioCell("git", "Git Push / PR", box_style(COLORS["gray_light"], COLORS["ink"]), 55, 190, 130, 60),
        DrawioCell("test", "Test<br>SAST·SCA·Secret Scan", box_style(COLORS["blue_light"], COLORS["blue"], 12), 225, 180, 170, 80),
        DrawioCell("build", "Container Build", box_style(COLORS["green_light"], COLORS["green"]), 435, 190, 145, 60),
        DrawioCell("scan", "Image Scan", box_style(COLORS["purple_light"], COLORS["purple"]), 620, 190, 135, 60),
        DrawioCell("ecr", "Amazon ECR", icon_style("ecr"), 790, 165, 100, 110),
        DrawioCell("cd", "자동 CD", box_style(COLORS["green_light"], COLORS["green"]), 925, 190, 120, 60),
        DrawioCell("eks", "EKS Test Namespace", icon_style("eks"), 1080, 165, 120, 110),
        DrawioCell("smoke", "Smoke Test", box_style(COLORS["blue_light"], COLORS["blue"]), 1235, 190, 130, 60),
        DrawioCell("attack", "통제된 공격·장애", box_style(COLORS["red_light"], COLORS["red"]), 1400, 190, 170, 60),
        DrawioCell("cw", "CloudWatch", icon_style("cloudwatch"), 1240, 335, 100, 105),
        DrawioCell("s3", "S3 Evidence", icon_style("s3"), 1360, 335, 100, 105),
        DrawioCell("compare", "Before / After 비교<br>탐지·차단·피해·재현성", box_style(COLORS["orange_light"], COLORS["orange"], 12), 930, 350, 220, 70),
        DrawioCell("infra_lane", "Infrastructure Pipeline · Terraform", group_style("#FBF8FF", COLORS["purple"]), 25, 520, 1630, 300),
        DrawioCell("tf", "Terraform 변경", box_style(COLORS["gray_light"], COLORS["ink"]), 70, 650, 150, 60),
        DrawioCell("validate", "fmt · validate<br>IaC Security Scan", box_style(COLORS["blue_light"], COLORS["blue"], 12), 275, 635, 185, 90),
        DrawioCell("plan", "terraform plan", box_style(COLORS["purple_light"], COLORS["purple"]), 515, 650, 150, 60),
        DrawioCell("approval", "보호된 승인 단계<br>비용·삭제·권한", box_style(COLORS["orange_light"], COLORS["orange"], 12), 720, 635, 190, 90),
        DrawioCell("apply", "terraform apply", box_style(COLORS["green_light"], COLORS["green"]), 965, 650, 150, 60),
        DrawioCell("verify", "AWS 실제 상태 확인<br>Runtime·비용·Security", box_style(COLORS["blue_light"], COLORS["blue"], 12), 1170, 635, 250, 90),
    ]
    for cell in cells:
        add_vertex(root, cell)

    for edge in [
        ("e1", "git", "test", COLORS["green"], False, ""),
        ("e2", "test", "build", COLORS["green"], False, ""),
        ("e3", "build", "scan", COLORS["green"], False, ""),
        ("e4", "scan", "ecr", COLORS["green"], False, ""),
        ("e5", "ecr", "cd", COLORS["green"], False, ""),
        ("e6", "cd", "eks", COLORS["green"], False, ""),
        ("e7", "eks", "smoke", COLORS["green"], False, ""),
        ("e8", "smoke", "attack", COLORS["green"], False, ""),
        ("e9", "attack", "cw", COLORS["orange"], True, ""),
        ("e10", "attack", "s3", COLORS["orange"], True, ""),
        ("e11", "cw", "compare", COLORS["orange"], True, ""),
        ("e12", "s3", "compare", COLORS["orange"], True, ""),
        ("e13", "compare", "git", COLORS["red"], False, "조치 후 동일 조건 재검증"),
        ("e14", "tf", "validate", COLORS["purple"], False, ""),
        ("e15", "validate", "plan", COLORS["purple"], False, ""),
        ("e16", "plan", "approval", COLORS["purple"], False, ""),
        ("e17", "approval", "apply", COLORS["purple"], False, ""),
        ("e18", "apply", "verify", COLORS["purple"], False, ""),
    ]:
        add_edge(root, *edge)
    return diagram


def write_drawio(path: Path):
    mxfile = ET.Element(
        "mxfile",
        {
            "host": "app.diagrams.net",
            "modified": "2026-07-28T00:00:00.000Z",
            "agent": "Codex",
            "version": "24.7.17",
            "type": "device",
            "compressed": "false",
        },
    )
    mxfile.append(runtime_drawio_page())
    mxfile.append(cicd_drawio_page())
    ET.indent(mxfile, space="  ")
    path.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        + ET.tostring(mxfile, encoding="unicode"),
        encoding="utf-8",
    )


def main():
    ensure_icon_package()
    missing = [str(icon_file(key)) for key in ICON_PATHS if not icon_file(key).exists()]
    if missing:
        raise FileNotFoundError(
            "AWS icon package is missing required files.\n"
            f"Download: {AWS_ICON_PACKAGE}\n"
            + "\n".join(missing)
        )

    runtime_png = OUTPUT_DIR / "3차프로젝트_AWS_Runtime_Target_Architecture.png"
    cicd_png = OUTPUT_DIR / "3차프로젝트_CICD_Security_Verification_Loop.png"
    drawio = OUTPUT_DIR / "3차프로젝트_AWS_Target_Architecture.drawio"

    draw_runtime_png(runtime_png)
    draw_cicd_png(cicd_png)
    write_drawio(drawio)

    print(runtime_png)
    print(cicd_png)
    print(drawio)


if __name__ == "__main__":
    main()
