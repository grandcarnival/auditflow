from __future__ import annotations

import re
import zipfile
from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any

from lxml import etree

from .openxml import NS


@dataclass(frozen=True)
class TextRun:
    text: str
    bold: bool
    italic: bool
    font_size: int | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SlideStructure:
    index: int
    part_name: str
    text: str
    text_runs: list[TextRun]
    placeholder_count: int
    table_count: int
    chart_count: int
    shape_count: int
    note_text: str | None
    role_hint: str
    layout_fingerprint: str
    semantic_placeholders: list[str]
    recurring_markers: list[str]
    is_title_content: bool

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["text_runs"] = [run.to_dict() for run in self.text_runs]
        return data


@dataclass(frozen=True)
class TemplateModel:
    slide_count: int
    slide_width_emu: int | None
    slide_height_emu: int | None
    slides: list[SlideStructure]

    def to_dict(self) -> dict[str, Any]:
        return {
            "slide_count": self.slide_count,
            "slide_width_emu": self.slide_width_emu,
            "slide_height_emu": self.slide_height_emu,
            "slides": [slide.to_dict() for slide in self.slides],
        }


def analyze_template(path: str | Path) -> TemplateModel:
    pptx_path = Path(path)
    with zipfile.ZipFile(pptx_path) as zf:
        names = sorted(zf.namelist())
        slide_names = sorted(name for name in names if _is_slide_part(name))
        notes = _read_notes(zf)
        width, height = _read_slide_size(zf)

        slides = [
            _analyze_slide(zf, slide_name, index, notes.get(index))
            for index, slide_name in enumerate(slide_names, start=1)
        ]

    return TemplateModel(
        slide_count=len(slides),
        slide_width_emu=width,
        slide_height_emu=height,
        slides=slides,
    )


def _analyze_slide(
    zf: zipfile.ZipFile,
    slide_name: str,
    index: int,
    note_text: str | None,
) -> SlideStructure:
    root = etree.fromstring(zf.read(slide_name))
    text_runs = _extract_text_runs(root)
    text = " ".join(run.text for run in text_runs if run.text)
    table_count = len(root.xpath(".//a:tbl", namespaces=NS))
    chart_count = _count_chart_relationships(zf, slide_name)
    placeholder_count = len(root.xpath(".//p:ph", namespaces=NS))
    shape_count = len(root.xpath(".//p:sp|.//p:graphicFrame|.//p:pic", namespaces=NS))
    semantic_placeholders = _semantic_placeholders(root, text=text, table_count=table_count, chart_count=chart_count)

    return SlideStructure(
        index=index,
        part_name=slide_name,
        text=text,
        text_runs=text_runs,
        placeholder_count=placeholder_count,
        table_count=table_count,
        chart_count=chart_count,
        shape_count=shape_count,
        note_text=note_text,
        role_hint=_classify_role(text=text, table_count=table_count, chart_count=chart_count, index=index),
        layout_fingerprint=_layout_fingerprint(root),
        semantic_placeholders=semantic_placeholders,
        recurring_markers=_recurring_markers(text),
        is_title_content=_is_title_content(semantic_placeholders, table_count, chart_count),
    )


def _extract_text_runs(root: etree._Element) -> list[TextRun]:
    runs: list[TextRun] = []
    for run in root.xpath(".//a:r", namespaces=NS):
        text_nodes = run.xpath(".//a:t", namespaces=NS)
        if not text_nodes:
            continue
        rpr = run.find("a:rPr", namespaces=NS)
        font_size = None
        if rpr is not None and rpr.get("sz"):
            font_size = int(rpr.get("sz")) // 100
        runs.append(
            TextRun(
                text="".join(node.text or "" for node in text_nodes),
                bold=rpr is not None and rpr.get("b") == "1",
                italic=rpr is not None and rpr.get("i") == "1",
                font_size=font_size,
            )
        )
    return runs


def _read_notes(zf: zipfile.ZipFile) -> dict[int, str]:
    notes: dict[int, str] = {}
    for name in sorted(zf.namelist()):
        match = re.fullmatch(r"ppt/notesSlides/notesSlide(\d+)\.xml", name)
        if not match:
            continue
        root = etree.fromstring(zf.read(name))
        text = " ".join(node.text or "" for node in root.xpath(".//a:t", namespaces=NS))
        notes[int(match.group(1))] = text
    return notes


def _read_slide_size(zf: zipfile.ZipFile) -> tuple[int | None, int | None]:
    if "ppt/presentation.xml" not in zf.namelist():
        return None, None
    root = etree.fromstring(zf.read("ppt/presentation.xml"))
    size = root.find("p:sldSz", namespaces=NS)
    if size is None:
        return None, None
    return _optional_int(size.get("cx")), _optional_int(size.get("cy"))


def _count_chart_relationships(zf: zipfile.ZipFile, slide_name: str) -> int:
    rel_name = slide_name.replace("ppt/slides/", "ppt/slides/_rels/") + ".rels"
    if rel_name not in zf.namelist():
        return 0
    root = etree.fromstring(zf.read(rel_name))
    return len([
        rel
        for rel in root
        if rel.get("Type", "").endswith("/chart")
    ])


def _classify_role(text: str, table_count: int, chart_count: int, index: int) -> str:
    lowered = text.lower()
    if index == 1:
        return "cover"
    if "executive summary" in lowered:
        return "executive_summary"
    if "finding" in lowered:
        return "finding_detail"
    if chart_count or table_count:
        return "metrics"
    return "content"


def _semantic_placeholders(root: etree._Element, text: str, table_count: int, chart_count: int) -> list[str]:
    values: list[str] = []
    for placeholder in root.xpath(".//p:ph", namespaces=NS):
        placeholder_type = placeholder.get("type")
        if placeholder_type:
            values.append(placeholder_type)
    lowered = text.lower()
    if "finding" in lowered:
        values.append("finding")
    if "executive summary" in lowered:
        values.append("summary")
    if table_count:
        values.append("table")
    if chart_count:
        values.append("chart")
    return sorted(set(values))


def _layout_fingerprint(root: etree._Element) -> str:
    descriptors: list[str] = []
    for node in root.xpath(".//p:sp|.//p:graphicFrame|.//p:pic", namespaces=NS):
        tag = etree.QName(node).localname
        xfrm = node.find(".//a:xfrm", namespaces=NS)
        off = xfrm.find("a:off", namespaces=NS) if xfrm is not None else None
        ext = xfrm.find("a:ext", namespaces=NS) if xfrm is not None else None
        placeholder = node.find(".//p:ph", namespaces=NS)
        descriptors.append("|".join([
            tag,
            placeholder.get("type", "") if placeholder is not None else "",
            off.get("x", "") if off is not None else "",
            off.get("y", "") if off is not None else "",
            ext.get("cx", "") if ext is not None else "",
            ext.get("cy", "") if ext is not None else "",
            str(len(node.xpath(".//a:tbl", namespaces=NS))),
            str(_has_chart_reference(node)),
        ]))
    return sha256("\n".join(sorted(descriptors)).encode("utf-8")).hexdigest()


def _recurring_markers(text: str) -> list[str]:
    lowered = text.lower()
    markers = []
    for key in ["executive summary", "finding detail", "risk", "recommendation", "condition"]:
        if key in lowered:
            markers.append(key)
    return markers


def _is_title_content(semantic_placeholders: list[str], table_count: int, chart_count: int) -> bool:
    content_signals = {"body", "obj", "finding", "summary", "table", "chart"}
    return "title" in semantic_placeholders and (
        bool(content_signals.intersection(semantic_placeholders)) or table_count > 0 or chart_count > 0
    )


def _has_chart_reference(node: etree._Element) -> bool:
    return bool(node.xpath(".//c:chart", namespaces=NS))


def _is_slide_part(name: str) -> bool:
    return bool(re.fullmatch(r"ppt/slides/slide\d+\.xml", name))


def _optional_int(value: str | None) -> int | None:
    return int(value) if value is not None else None
