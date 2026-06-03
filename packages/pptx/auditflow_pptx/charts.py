from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Any

from lxml import etree
from openpyxl import load_workbook

from .openxml import NS, REL_NS, read_package, serialize_xml, write_package


@dataclass(frozen=True)
class ChartSeries:
    name: str
    values: list[float | int]

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "values": self.values}


@dataclass(frozen=True)
class ChartUpdateResult:
    chart_index: int
    categories: list[str]
    series: list[ChartSeries]
    embedded_workbook_updated: bool
    series_count_preserved: bool
    relationship_preserved: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "chart_index": self.chart_index,
            "categories": self.categories,
            "series": [item.to_dict() for item in self.series],
            "embedded_workbook_updated": self.embedded_workbook_updated,
            "series_count_preserved": self.series_count_preserved,
            "relationship_preserved": self.relationship_preserved,
        }


def update_chart_in_clone(
    source: str | Path,
    target: str | Path,
    categories: list[str],
    series: list[ChartSeries],
    chart_index: int = 1,
) -> ChartUpdateResult:
    infos, parts = read_package(source)
    chart_name = f"ppt/charts/chart{chart_index}.xml"
    rels_name = f"ppt/charts/_rels/chart{chart_index}.xml.rels"
    if chart_name not in parts:
        raise ValueError(f"Chart {chart_index} was not found.")

    chart_root = etree.fromstring(parts[chart_name])
    existing_series = chart_root.xpath(".//c:ser", namespaces=NS)
    original_series_count = len(existing_series)
    if not existing_series:
        raise ValueError("Chart has no series to update.")

    _resize_series(existing_series, len(series))
    updated_series = chart_root.xpath(".//c:ser", namespaces=NS)
    for index, (series_node, item) in enumerate(zip(updated_series, series)):
        _set_series_xml(series_node, index, item, categories)

    parts[chart_name] = serialize_xml(chart_root)

    embedded_workbook_updated = False
    relationship_preserved = rels_name in parts
    if rels_name in parts:
        workbook_part = _embedded_workbook_part(parts[rels_name])
        if workbook_part and workbook_part in parts:
            parts[workbook_part] = _updated_workbook(parts[workbook_part], categories, series)
            embedded_workbook_updated = True

    write_package(target, infos, parts)
    return ChartUpdateResult(
        chart_index=chart_index,
        categories=categories,
        series=series,
        embedded_workbook_updated=embedded_workbook_updated,
        series_count_preserved=original_series_count == len(series),
        relationship_preserved=relationship_preserved,
    )


def extract_chart_data(path: str | Path, chart_index: int = 1) -> dict[str, Any]:
    _, parts = read_package(path)
    chart_name = f"ppt/charts/chart{chart_index}.xml"
    root = etree.fromstring(parts[chart_name])
    series_data = []
    categories: list[str] = []
    for series_node in root.xpath(".//c:ser", namespaces=NS):
        if not categories:
            categories = _cache_values(series_node, ".//c:cat//c:pt")
        series_data.append({
            "name": (_cache_values(series_node, ".//c:tx//c:pt") or [""])[0],
            "values": [_coerce_number(value) for value in _cache_values(series_node, ".//c:val//c:pt")],
        })
    return {"categories": categories, "series": series_data}


def _resize_series(existing_series: list[etree._Element], desired_count: int) -> None:
    parent = existing_series[0].getparent()
    while len(existing_series) > desired_count:
        parent.remove(existing_series[-1])
        existing_series = parent.xpath("./c:ser", namespaces=NS)
    while len(existing_series) < desired_count:
        clone = etree.fromstring(etree.tostring(existing_series[-1]))
        parent.insert(parent.index(existing_series[-1]) + 1, clone)
        existing_series = parent.xpath("./c:ser", namespaces=NS)


def _set_series_xml(series_node: etree._Element, index: int, series: ChartSeries, categories: list[str]) -> None:
    _set_val(series_node, "./c:idx", str(index))
    _set_val(series_node, "./c:order", str(index))
    _set_text_cache(series_node, ".//c:tx/c:strRef", [series.name])
    _set_text_cache(series_node, ".//c:cat/c:strRef", categories)
    _set_number_cache(series_node, ".//c:val/c:numRef", series.values)
    _set_formula(series_node, ".//c:tx/c:strRef/c:f", f"Sheet1!${_col(index + 2)}$1")
    _set_formula(series_node, ".//c:cat/c:strRef/c:f", f"Sheet1!$A$2:$A${len(categories) + 1}")
    _set_formula(series_node, ".//c:val/c:numRef/c:f", f"Sheet1!${_col(index + 2)}$2:${_col(index + 2)}${len(categories) + 1}")


def _set_val(series_node: etree._Element, xpath: str, value: str) -> None:
    nodes = series_node.xpath(xpath, namespaces=NS)
    if nodes:
        nodes[0].set("val", value)


def _set_formula(series_node: etree._Element, xpath: str, value: str) -> None:
    nodes = series_node.xpath(xpath, namespaces=NS)
    if nodes:
        nodes[0].text = value


def _set_text_cache(series_node: etree._Element, ref_xpath: str, values: list[str]) -> None:
    refs = series_node.xpath(ref_xpath, namespaces=NS)
    if not refs:
        return
    ref = refs[0]
    cache = ref.find("c:strCache", namespaces=NS)
    if cache is None:
        cache = etree.SubElement(ref, f"{{{NS['c']}}}strCache")
    _replace_cache_points(cache, [str(value) for value in values])


def _set_number_cache(series_node: etree._Element, ref_xpath: str, values: list[float | int]) -> None:
    refs = series_node.xpath(ref_xpath, namespaces=NS)
    if not refs:
        return
    ref = refs[0]
    cache = ref.find("c:numCache", namespaces=NS)
    if cache is None:
        cache = etree.SubElement(ref, f"{{{NS['c']}}}numCache")
    format_code = cache.find("c:formatCode", namespaces=NS)
    for child in list(cache):
        if child is not format_code:
            cache.remove(child)
    _ensure_pt_count(cache, len(values), after=format_code)
    for index, value in enumerate(values):
        pt = etree.SubElement(cache, f"{{{NS['c']}}}pt", idx=str(index))
        v = etree.SubElement(pt, f"{{{NS['c']}}}v")
        v.text = _format_number(value)


def _replace_cache_points(cache: etree._Element, values: list[str]) -> None:
    for child in list(cache):
        cache.remove(child)
    _ensure_pt_count(cache, len(values))
    for index, value in enumerate(values):
        pt = etree.SubElement(cache, f"{{{NS['c']}}}pt", idx=str(index))
        v = etree.SubElement(pt, f"{{{NS['c']}}}v")
        v.text = value


def _ensure_pt_count(cache: etree._Element, count: int, after: etree._Element | None = None) -> None:
    pt_count = etree.Element(f"{{{NS['c']}}}ptCount", val=str(count))
    if after is not None:
        cache.insert(cache.index(after) + 1, pt_count)
    else:
        cache.insert(0, pt_count)


def _embedded_workbook_part(rels_xml: bytes) -> str | None:
    root = etree.fromstring(rels_xml)
    for rel in root:
        if rel.get("Type", "").endswith("/package"):
            target = rel.get("Target", "")
            if target.startswith("../"):
                return "ppt/" + target[3:]
            return "ppt/charts/" + target
    return None


def _updated_workbook(
    workbook_bytes: bytes,
    categories: list[str],
    series: list[ChartSeries],
) -> bytes:
    workbook = load_workbook(BytesIO(workbook_bytes))
    sheet = workbook.active
    for row in sheet.iter_rows():
        for cell in row:
            cell.value = None
    sheet.cell(row=1, column=1, value="")
    for col_index, item in enumerate(series, start=2):
        sheet.cell(row=1, column=col_index, value=item.name)
    for row_index, category in enumerate(categories, start=2):
        sheet.cell(row=row_index, column=1, value=category)
        for col_index, item in enumerate(series, start=2):
            value_index = row_index - 2
            sheet.cell(row=row_index, column=col_index, value=item.values[value_index] if value_index < len(item.values) else None)
    stream = BytesIO()
    workbook.save(stream)
    return stream.getvalue()


def _cache_values(series_node: etree._Element, xpath: str) -> list[str]:
    values = []
    for point in series_node.xpath(xpath, namespaces=NS):
        node = point.find("c:v", namespaces=NS)
        values.append(node.text or "" if node is not None else "")
    return values


def _coerce_number(value: str) -> int | float | str:
    try:
        parsed = float(value)
    except ValueError:
        return value
    return int(parsed) if parsed.is_integer() else parsed


def _format_number(value: float | int) -> str:
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _col(index: int) -> str:
    value = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        value = chr(65 + remainder) + value
    return value

