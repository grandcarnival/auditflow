from __future__ import annotations

import hashlib
import copy
import re
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from lxml import etree


NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "c": "http://schemas.openxmlformats.org/drawingml/2006/chart",
}

REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"


@dataclass(frozen=True)
class PptxMetrics:
    path: str
    sha256: str
    size_bytes: int
    slide_count: int
    slide_master_count: int
    slide_layout_count: int
    theme_count: int
    notes_count: int
    chart_count: int
    table_count: int
    image_count: int
    editable_text_run_count: int
    placeholder_count: int
    package_part_count: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def collect_metrics(path: str | Path) -> PptxMetrics:
    pptx_path = Path(path)
    file_data = pptx_path.read_bytes()
    with zipfile.ZipFile(pptx_path) as zf:
        names = sorted(zf.namelist())
        slide_names = [name for name in names if _is_slide_part(name)]
        table_count = 0
        editable_text_run_count = 0
        placeholder_count = 0

        for slide_name in slide_names:
            root = _parse_xml(zf.read(slide_name))
            table_count += len(root.xpath(".//a:tbl", namespaces=NS))
            editable_text_run_count += len(root.xpath(".//a:r", namespaces=NS))
            placeholder_count += len(root.xpath(".//p:ph", namespaces=NS))

        return PptxMetrics(
            path=str(pptx_path),
            sha256=_sha256(file_data),
            size_bytes=len(file_data),
            slide_count=len(slide_names),
            slide_master_count=_count(names, r"ppt/slideMasters/slideMaster\d+\.xml"),
            slide_layout_count=_count(names, r"ppt/slideLayouts/slideLayout\d+\.xml"),
            theme_count=_count(names, r"ppt/theme/theme\d+\.xml"),
            notes_count=_count(names, r"ppt/notesSlides/notesSlide\d+\.xml"),
            chart_count=_count(names, r"ppt/charts/chart\d+\.xml"),
            table_count=table_count,
            image_count=len([name for name in names if name.startswith("ppt/media/")]),
            editable_text_run_count=editable_text_run_count,
            placeholder_count=placeholder_count,
            package_part_count=len(names),
        )


def extract_slide_text(path: str | Path) -> list[str]:
    pptx_path = Path(path)
    slides: list[str] = []
    with zipfile.ZipFile(pptx_path) as zf:
        for slide_name in sorted(name for name in zf.namelist() if _is_slide_part(name)):
            root = _parse_xml(zf.read(slide_name))
            text = " ".join(node.text or "" for node in root.xpath(".//a:t", namespaces=NS))
            slides.append(text)
    return slides


def replace_text_in_clone(
    source: str | Path,
    target: str | Path,
    replacements: dict[str, str],
    slide_index: int | None = None,
) -> None:
    source_path = Path(source)
    target_path = Path(target)
    target_path.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(source_path, "r") as zin, zipfile.ZipFile(
        target_path,
        "w",
        compression=zipfile.ZIP_DEFLATED,
    ) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if _is_slide_part(item.filename) and (slide_index is None or item.filename == f"ppt/slides/slide{slide_index}.xml"):
                data = _replace_text_nodes(data, replacements)
            zout.writestr(item, data)


def validate_preservation(source: str | Path, target: str | Path, allow_slide_additions: bool = False) -> dict[str, Any]:
    source_metrics = collect_metrics(source)
    target_metrics = collect_metrics(target)
    checks = {
        "slide_count": (
            target_metrics.slide_count >= source_metrics.slide_count
            if allow_slide_additions
            else source_metrics.slide_count == target_metrics.slide_count
        ),
        "masters_preserved": target_metrics.slide_master_count >= source_metrics.slide_master_count,
        "layouts_preserved": target_metrics.slide_layout_count >= source_metrics.slide_layout_count,
        "themes_preserved": target_metrics.theme_count >= source_metrics.theme_count,
        "notes_preserved": target_metrics.notes_count >= source_metrics.notes_count,
        "charts_preserved": target_metrics.chart_count >= source_metrics.chart_count,
        "tables_preserved": target_metrics.table_count >= source_metrics.table_count,
        "editable_text_present": target_metrics.editable_text_run_count > 0,
    }
    passed = sum(1 for value in checks.values() if value)
    return {
        "checks": checks,
        "passed": passed,
        "total": len(checks),
        "score": round(passed / len(checks), 3),
        "source": source_metrics.to_dict(),
        "target": target_metrics.to_dict(),
    }


def _replace_text_nodes(data: bytes, replacements: dict[str, str]) -> bytes:
    try:
        root = _parse_xml(data)
    except etree.XMLSyntaxError:
        return data

    changed = False
    for node in root.xpath(".//a:t", namespaces=NS):
        if node.text in replacements:
            node.text = replacements[node.text]
            changed = True

    for body in root.xpath(".//p:sp/p:txBody", namespaces=NS):
        if _replace_text_body(body, replacements):
            changed = True

    if not changed:
        return data
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)


def _replace_text_body(body: etree._Element, replacements: dict[str, str]) -> bool:
    paragraphs = body.xpath("./a:p", namespaces=NS)
    if not paragraphs:
        return False
    paragraph_text = [_paragraph_text(paragraph) for paragraph in paragraphs]
    joined = "\n".join(text for text in paragraph_text if text)
    if joined not in replacements:
        return False

    replacement_lines = replacements[joined].split("\n")
    while len(paragraphs) < len(replacement_lines):
        paragraphs.append(copy.deepcopy(paragraphs[-1]))
        body.append(paragraphs[-1])
    while len(paragraphs) > len(replacement_lines):
        body.remove(paragraphs[-1])
        paragraphs.pop()

    for paragraph, line in zip(paragraphs, replacement_lines):
        _set_paragraph_text(paragraph, line)
    return True


def _paragraph_text(paragraph: etree._Element) -> str:
    return "".join(node.text or "" for node in paragraph.xpath(".//a:t", namespaces=NS))


def _set_paragraph_text(paragraph: etree._Element, text: str) -> None:
    text_nodes = paragraph.xpath(".//a:t", namespaces=NS)
    if text_nodes:
        text_nodes[0].text = text
        for node in text_nodes[1:]:
            node.text = ""
        return
    run = etree.SubElement(paragraph, f"{{{NS['a']}}}r")
    node = etree.SubElement(run, f"{{{NS['a']}}}t")
    node.text = text


def _parse_xml(data: bytes) -> etree._Element:
    return etree.fromstring(data)


def serialize_xml(root: etree._Element) -> bytes:
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)


def read_package(source: str | Path) -> tuple[list[zipfile.ZipInfo], dict[str, bytes]]:
    with zipfile.ZipFile(source, "r") as zin:
        return zin.infolist(), {name: zin.read(name) for name in zin.namelist()}


def write_package(target: str | Path, infos: list[zipfile.ZipInfo], parts: dict[str, bytes]) -> None:
    target_path = Path(target)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    written: set[str] = set()
    with zipfile.ZipFile(target_path, "w", compression=zipfile.ZIP_DEFLATED) as zout:
        for info in infos:
            if info.filename in parts and info.filename not in written:
                zout.writestr(info, parts[info.filename])
                written.add(info.filename)
        for name, data in sorted(parts.items()):
            if name not in written:
                zout.writestr(name, data)
                written.add(name)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _is_slide_part(name: str) -> bool:
    return bool(re.fullmatch(r"ppt/slides/slide\d+\.xml", name))


def _count(names: list[str], pattern: str) -> int:
    return len([name for name in names if re.fullmatch(pattern, name)])
