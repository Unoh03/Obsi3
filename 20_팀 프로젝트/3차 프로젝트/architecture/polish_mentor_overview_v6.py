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
    # V6 geometry stays fixed. Only small baseline and height corrections are allowed.
    "dr-s3": (2080, 650, 190, 150),
    "ecr": (270, 650, 190, 150),
    "p-s3": (500, 650, 190, 150),
    "p-alb": (910, 1005, 180, 155),
    "p-eks": (910, 1180, 180, 150),
    "pod-identity": (1100, 1180, 180, 150),
    "dr-alb": (2420, 1005, 180, 155),
    "dr-eks": (2420, 1180, 180, 150),
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
    "e-cf-alb": [(550, 505), (1000, 505), (1000, 940)],
    "e-argo-peks": [(1095, 1398), (1095, 1255)],
    "e-ssm-pbastion": [(1190, 500), (220, 500), (220, 930), (730, 930)],
    "e-ssm-drbastion": [(1190, 500), (2005, 500), (2005, 930), (2250, 930)],
    "e-iam-pod": [(970, 520), (1190, 520), (1190, 1170)],
    "e-pbastion-peks": [(850, 1075), (895, 1075), (895, 1277)],
    "e-drbastion-dreks": [(2360, 1075), (2380, 1075), (2380, 1253), (2400, 1253)],
    "e-peks-data": [(991, 1515), (650, 1515)],
    "e-rds-replication": [(650, 1720), (2240, 1720)],
    "e-s3-replication": [(595, 815), (2175, 815)],
    "e-repo-argo": [(1310, 860), (1310, 1398), (1290, 1398)],
    "e-operator-bastion": [(400, 995), (400, 930), (730, 930)],
    "e-ecr-peks": [(365, 825), (875, 825), (875, 1221), (900, 1221)],
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
        update_style(cell, fontSize=25, imageWidth=82, imageHeight=82)
        cell.set("value", bump_html_sizes(cell.get("value", ""), {23: 25, 22: 24, 18: 19, 17: 18}))

    # Compact cells need extra headroom for their captions.
    for cell_id in {"acm", "waf", "p-bastion", "dr-bastion"}:
        update_style(cell_map[cell_id], imageWidth=70, imageHeight=70, fontSize=24)

    for cell_id in SUBNET_IDS:
        cell = cell_map[cell_id]
        update_style(cell, fontSize=26, imageWidth=34, imageHeight=34, spacingLeft=52)
        mapping = {22: 23, 18: 18, 17: 18} if cell_id.startswith("dr-") else {23: 24, 18: 19}
        cell.set("value", bump_html_sizes(cell.get("value", ""), mapping))

    # Reserve the right side of the 2a / 1a public subnet labels for Bastion icons.
    update_style(cell_map["p-2a-public"], spacingRight=175)

    for cell_id in REGION_VPC_IDS:
        cell = cell_map[cell_id]
        update_style(cell, fontSize=28, imageWidth=36, imageHeight=36, spacingLeft=54)
        cell.set("value", bump_html_sizes(cell.get("value", ""), {32: 34, 20: 21}))

    for cell_id in {"edge-zone", "primary-regional-services", "dr-regional-services", "observability", "local-tools"}:
        cell = cell_map[cell_id]
        update_style(cell, fontSize=26)
        cell.set(
            "value",
            bump_html_sizes(cell.get("value", ""), {29: 31, 26: 28, 24: 26, 19: 20, 18: 19}),
        )

    for cell_id in {"p-az-a", "p-az-c", "dr-az-a", "dr-az-c"}:
        cell = cell_map[cell_id]
        update_style(cell, fontSize=25)
        cell.set("value", bump_html_sizes(cell.get("value", ""), {24: 25}))

    for cell_id in {"p-multi-az-lane", "dr-multi-az-lane"}:
        cell = cell_map[cell_id]
        update_style(cell, fontSize=23)
        cell.set("value", bump_html_sizes(cell.get("value", ""), {22: 23, 18: 19}))

    for cell_id in {"primary-data", "dr-data"}:
        cell = cell_map[cell_id]
        update_style(cell, fontSize=22)
        cell.set("value", bump_html_sizes(cell.get("value", ""), {20: 22, 18: 19}))

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
        update_style(edge, fontSize=20, labelBackgroundColor="#FFFFFF")

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
    # Binary output keeps LF line endings so Git does not flag Windows CR as trailing whitespace.
    with TARGET.open("wb") as stream:
        tree.write(stream, encoding="utf-8", xml_declaration=True)
    print(f"WROTE {TARGET}")
    print(f"VALIDATED {len(after_vertices)} vertices / {len(after_edges)} edges")


if __name__ == "__main__":
    main()
