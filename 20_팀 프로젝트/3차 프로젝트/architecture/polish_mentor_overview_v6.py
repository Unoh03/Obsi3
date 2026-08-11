from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path


HERE = Path(__file__).resolve().parent
SOURCE = HERE / "06_MENTOR_OVERVIEW__LARGE_TEXT__v6.drawio"
TARGET = HERE / "06_MENTOR_OVERVIEW__FINAL__v6.drawio"


SERVICE_IDS = {
    "route53",
    "cloudfront",
    "acm",
    "waf",
    "iam",
    "ssm",
    "ecr",
    "p-s3",
    "p-alb",
    "p-bastion",
    "p-eks",
    "pod-identity",
    "p-rds",
    "p-valkey",
    "p-efs",
    "dr-s3",
    "dr-alb",
    "dr-bastion",
    "dr-eks",
    "dr-rds",
    "dr-valkey",
    "dr-efs",
    "cloudtrail",
    "guardduty",
    "eventbridge",
    "sns",
    "cloudwatch",
    "security-s3",
}

SUBNET_IDS = {
    "p-2a-public",
    "p-2a-private",
    "p-2a-database",
    "p-2c-public",
    "p-2c-private",
    "p-2c-database",
    "dr-1a-public",
    "dr-1a-private",
    "dr-1a-database",
    "dr-1c-public",
    "dr-1c-private",
    "dr-1c-database",
}

REGION_VPC_IDS = {"aws-cloud", "primary-region", "dr-region", "primary-vpc", "dr-vpc"}

SECTION_IDS = {
    "edge-zone",
    "primary-regional-services",
    "dr-regional-services",
    "p-multi-az-lane",
    "p-az-a",
    "p-az-c",
    "dr-multi-az-lane",
    "dr-az-a",
    "dr-az-c",
    "primary-data",
    "dr-data",
    "observability",
    "local-tools",
}

NOTE_IDS = {"lifecycle-note", "primary-sg-note", "dr-note", "local-detail"}

EXTERNAL_IDS = {"actor", "github", "git-repo", "operator-pc", "argocd", "grafana", "waf-viewer"}


GEOMETRY = {
    # V6 skeleton retained; horizontal space is rebalanced so DR is no longer cramped.
    "primary-region": (190, 540, 1650, 1240),
    "dr-region": (1870, 540, 1140, 1240),
    "primary-regional-services": (230, 610, 1570, 190),
    "dr-regional-services": (1910, 610, 1060, 190),
    "primary-vpc": (230, 850, 1570, 900),
    "dr-vpc": (1910, 850, 1060, 900),
    "p-az-a": (270, 950, 515, 520),
    "p-multi-az-lane": (805, 950, 390, 520),
    "p-az-c": (1215, 950, 545, 520),
    "dr-az-a": (1940, 950, 320, 520),
    "dr-multi-az-lane": (2280, 950, 320, 520),
    "dr-az-c": (2620, 950, 320, 520),
    "p-2a-public": (290, 1010, 475, 130),
    "p-2a-private": (290, 1150, 475, 150),
    "p-2a-database": (290, 1310, 475, 130),
    "p-2c-public": (1235, 1010, 505, 130),
    "p-2c-private": (1235, 1150, 505, 150),
    "p-2c-database": (1235, 1310, 505, 130),
    "dr-1a-public": (1955, 1010, 290, 130),
    "dr-1a-private": (1955, 1150, 290, 150),
    "dr-1a-database": (1955, 1310, 290, 130),
    "dr-1c-public": (2635, 1010, 290, 130),
    "dr-1c-private": (2635, 1150, 290, 150),
    "dr-1c-database": (2635, 1310, 290, 130),
    "dr-data": (1960, 1475, 950, 225),
    "dr-s3": (1930, 650, 190, 145),
    "dr-note": (2160, 655, 780, 130),
    "p-alb": (815, 1005, 180, 150),
    "p-eks": (815, 1180, 180, 150),
    "pod-identity": (1005, 1180, 180, 150),
    "argocd": (1005, 1340, 180, 115),
    "p-bastion": (595, 1015, 160, 120),
    "dr-alb": (2340, 1005, 200, 150),
    "dr-eks": (2340, 1180, 200, 150),
    "dr-bastion": (2085, 1015, 150, 120),
    "dr-rds": (2010, 1530, 190, 165),
    "dr-valkey": (2320, 1530, 190, 165),
    "dr-efs": (2630, 1530, 190, 165),
    "ecr": (270, 650, 190, 145),
    "p-s3": (500, 650, 190, 145),
    "p-rds": (550, 1530, 200, 165),
    "p-valkey": (990, 1530, 200, 165),
    "p-efs": (1430, 1530, 200, 165),
    "cloudtrail": (250, 1880, 180, 165),
    "guardduty": (470, 1880, 180, 165),
    "eventbridge": (690, 1880, 180, 165),
    "sns": (910, 1880, 180, 165),
    "cloudwatch": (1130, 1880, 190, 165),
    "security-s3": (1360, 1880, 200, 165),
    "local-detail": (1730, 1875, 1200, 180),
    "grafana": (1090, 2230, 310, 125),
    "waf-viewer": (1480, 2230, 330, 125),
}


EDGE_POINTS = {
    "e-cf-alb": [(550, 505), (905, 505), (905, 940)],
    "e-argo-peks": [(1000, 1398), (1000, 1255)],
    "e-ssm-pbastion": [(1190, 500), (220, 500), (220, 930), (675, 930)],
    "e-ssm-drbastion": [(1190, 500), (1855, 500), (1855, 930), (2160, 930)],
    "e-iam-pod": [(970, 520), (1095, 520), (1095, 1170)],
    "e-pbastion-peks": [(790, 1075), (790, 1277), (805, 1277)],
    "e-drbastion-dreks": [(2268, 1075), (2268, 1253), (2330, 1253)],
    "e-peks-data": [(905, 1515), (650, 1515)],
    "e-rds-replication": [(650, 1720), (2105, 1720)],
    "e-s3-replication": [(595, 815), (2025, 815)],
    "e-repo-argo": [(1205, 860), (1205, 1398), (1195, 1398)],
    "e-operator-bastion": [(400, 995), (400, 930), (675, 930)],
    "e-ecr-peks": [(365, 825), (790, 825), (790, 1221), (805, 1221)],
}


EDGE_ENTRY_TOP = {"e-ssm-pbastion", "e-ssm-drbastion", "e-operator-bastion"}


def set_style(style: str, key: str, value: str | int | float) -> str:
    pattern = re.compile(rf"(^|;){re.escape(key)}=[^;]*(?=;|$)")
    replacement = rf"\1{key}={value}"
    if pattern.search(style):
        return pattern.sub(replacement, style, count=1)
    if style and not style.endswith(";"):
        style += ";"
    return f"{style}{key}={value};"


def update_style(cell: ET.Element, **values: str | int | float) -> None:
    style = cell.get("style", "")
    for key, value in values.items():
        style = set_style(style, key, value)
    cell.set("style", style)


def bump_html_sizes(value: str, mapping: dict[int, int]) -> str:
    def replace(match: re.Match[str]) -> str:
        old = int(match.group(1))
        return f"font-size:{mapping.get(old, old)}px"

    return re.sub(r"font-size:(\d+)px", replace, value)


def set_geometry(cell: ET.Element, geometry: tuple[int, int, int, int]) -> None:
    x, y, width, height = geometry
    node = cell.find("mxGeometry")
    if node is None:
        raise ValueError(f"{cell.get('id')}: mxGeometry missing")
    node.set("x", str(x))
    node.set("y", str(y))
    node.set("width", str(width))
    node.set("height", str(height))


def set_edge_points(cell: ET.Element, points: list[tuple[int, int]]) -> None:
    geometry = cell.find("mxGeometry")
    if geometry is None:
        raise ValueError(f"{cell.get('id')}: edge geometry missing")
    array = geometry.find("Array[@as='points']")
    if array is None:
        array = ET.SubElement(geometry, "Array", {"as": "points"})
    for child in list(array):
        array.remove(child)
    for x, y in points:
        ET.SubElement(array, "mxPoint", {"x": str(x), "y": str(y)})


def ids_by_kind(root: ET.Element, attribute: str) -> set[str]:
    return {cell.get("id", "") for cell in root.findall(f".//mxCell[@{attribute}='1']")}


def main() -> None:
    tree = ET.parse(SOURCE)
    root = tree.getroot()
    before_vertices = ids_by_kind(root, "vertex")
    before_edges = ids_by_kind(root, "edge")
    cell_map = {cell.get("id", ""): cell for cell in root.findall(".//mxCell")}

    diagram = root.find("diagram")
    if diagram is None:
        raise ValueError("diagram missing")
    diagram.set("name", "06 · FINAL")
    root.set("agent", "Codex · AWS Official Architecture Groups · V6 Final Polish")

    cell_map["header-title"].set(
        "value",
        '<div style="text-align:left;">'
        '<span style="font-size:46px;color:#161E2D;font-weight:700;">AWS 멀티 리전 인프라</span><br>'
        '<span style="font-size:24px;color:#687078;">Terraform · GitOps · 서울 Primary / 도쿄 DR · 보안·관측·운영 흐름</span>'
        "</div>",
    )

    for cell_id, geometry in GEOMETRY.items():
        set_geometry(cell_map[cell_id], geometry)

    for cell_id in SERVICE_IDS:
        cell = cell_map[cell_id]
        update_style(cell, fontSize=26, imageWidth=88, imageHeight=88)
        cell.set("value", bump_html_sizes(cell.get("value", ""), {23: 26, 22: 25, 18: 20, 17: 19}))

    # The two Bastion cells are intentionally narrower than other service cells.
    for cell_id in {"p-bastion", "dr-bastion"}:
        update_style(cell_map[cell_id], imageWidth=82, imageHeight=82, fontSize=24)

    for cell_id in SUBNET_IDS:
        cell = cell_map[cell_id]
        update_style(cell, fontSize=27, imageWidth=36, imageHeight=36, spacingLeft=54)
        cell.set("value", bump_html_sizes(cell.get("value", ""), {23: 25, 22: 24, 18: 20, 17: 19}))

    # Reserve the right side of the 2a / 1a public subnet labels for Bastion icons.
    update_style(cell_map["p-2a-public"], spacingRight=175)
    update_style(cell_map["dr-1a-public"], spacingRight=120)

    for cell_id in REGION_VPC_IDS:
        cell = cell_map[cell_id]
        update_style(cell, fontSize=28, imageWidth=36, imageHeight=36, spacingLeft=54)
        cell.set("value", bump_html_sizes(cell.get("value", ""), {32: 35, 20: 22}))

    for cell_id in SECTION_IDS:
        cell = cell_map[cell_id]
        update_style(cell, fontSize=26)
        cell.set(
            "value",
            bump_html_sizes(cell.get("value", ""), {29: 31, 26: 29, 24: 26, 22: 24, 20: 22, 19: 21, 18: 20}),
        )

    for cell_id in NOTE_IDS:
        cell = cell_map[cell_id]
        update_style(cell, fontSize=21)
        cell.set("value", bump_html_sizes(cell.get("value", ""), {28: 30, 24: 26, 20: 22, 19: 21}))

    for cell_id in EXTERNAL_IDS:
        cell = cell_map[cell_id]
        update_style(cell, fontSize=24)
        cell.set("value", bump_html_sizes(cell.get("value", ""), {24: 26, 23: 25, 19: 21, 18: 20}))

    # The lifecycle block is presentation text, not a dense footnote.
    lifecycle = cell_map["lifecycle-note"]
    lifecycle.set("value", bump_html_sizes(lifecycle.get("value", ""), {30: 32, 22: 23}))

    for edge in root.findall(".//mxCell[@edge='1']"):
        update_style(edge, fontSize=21, labelBackgroundColor="#FFFFFF")

    for edge_id, points in EDGE_POINTS.items():
        set_edge_points(cell_map[edge_id], points)

    for edge_id in EDGE_ENTRY_TOP:
        update_style(cell_map[edge_id], entryX=0.5, entryY=0, entryDx=0, entryDy=0)

    # These words are already carried by the adjacent service captions and the operations note.
    # Keeping the arrows while removing duplicate labels prevents the observability row from reading as one sentence.
    cell_map["e-gd-eb"].set("value", "")
    cell_map["e-eb-sns"].set("value", "")
    cell_map["e-iam-pod"].set("value", "")

    after_vertices = ids_by_kind(root, "vertex")
    after_edges = ids_by_kind(root, "edge")
    if before_vertices != after_vertices:
        raise AssertionError("vertex ID set changed")
    if before_edges != after_edges:
        raise AssertionError("edge ID set changed")
    if len(after_vertices) != 71 or len(after_edges) != 23:
        raise AssertionError(f"unexpected topology count: {len(after_vertices)} vertices, {len(after_edges)} edges")

    for edge in root.findall(".//mxCell[@edge='1']"):
        if edge.get("source") not in after_vertices or edge.get("target") not in after_vertices:
            raise AssertionError(f"dangling edge: {edge.get('id')}")

    ET.indent(tree, space="  ")
    tree.write(TARGET, encoding="utf-8", xml_declaration=True)
    print(f"WROTE {TARGET}")
    print(f"VALIDATED {len(after_vertices)} vertices / {len(after_edges)} edges")


if __name__ == "__main__":
    main()
