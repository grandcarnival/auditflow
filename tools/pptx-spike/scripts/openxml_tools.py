from __future__ import annotations

import hashlib
import json
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


@dataclass
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
    slide_text: list[str]
    slide_part_hashes: dict[str, str]
    has_vba: bool


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def list_parts(path: Path) -> list[str]:
    with zipfile.ZipFile(path) as zf:
        return sorted(zf.namelist())


def read_part(path: Path, part_name: str) -> bytes:
    with zipfile.ZipFile(path) as zf:
        return zf.read(part_name)


def parse_xml(data: bytes) -> etree._Element:
    return etree.fromstring(data)


def is_slide_part(name: str) -> bool:
    return bool(re.fullmatch(r"ppt/slides/slide\d+\.xml", name))


def collect_metrics(path: Path) -> PptxMetrics:
    with zipfile.ZipFile(path) as zf:
        names = sorted(zf.namelist())
        slide_names = [name for name in names if is_slide_part(name)]
        slide_master_names = [name for name in names if re.fullmatch(r"ppt/slideMasters/slideMaster\d+\.xml", name)]
        slide_layout_names = [name for name in names if re.fullmatch(r"ppt/slideLayouts/slideLayout\d+\.xml", name)]
        theme_names = [name for name in names if re.fullmatch(r"ppt/theme/theme\d+\.xml", name)]
        notes_names = [name for name in names if re.fullmatch(r"ppt/notesSlides/notesSlide\d+\.xml", name)]
        chart_names = [name for name in names if re.fullmatch(r"ppt/charts/chart\d+\.xml", name)]
        image_names = [name for name in names if name.startswith("ppt/media/")]

        table_count = 0
        editable_text_run_count = 0
        placeholder_count = 0
        slide_text: list[str] = []
        slide_hashes: dict[str, str] = {}

        for slide_name in slide_names:
            data = zf.read(slide_name)
            slide_hashes[slide_name] = sha256_bytes(data)
            root = parse_xml(data)
            table_count += len(root.xpath(".//a:tbl", namespaces=NS))
            editable_text_run_count += len(root.xpath(".//a:r", namespaces=NS))
            placeholder_count += len(root.xpath(".//p:ph", namespaces=NS))
            texts = [node.text or "" for node in root.xpath(".//a:t", namespaces=NS)]
            slide_text.append(" ".join(texts))

        file_data = path.read_bytes()
        return PptxMetrics(
            path=str(path),
            sha256=sha256_bytes(file_data),
            size_bytes=len(file_data),
            slide_count=len(slide_names),
            slide_master_count=len(slide_master_names),
            slide_layout_count=len(slide_layout_names),
            theme_count=len(theme_names),
            notes_count=len(notes_names),
            chart_count=len(chart_names),
            table_count=table_count,
            image_count=len(image_names),
            editable_text_run_count=editable_text_run_count,
            placeholder_count=placeholder_count,
            package_part_count=len(names),
            slide_text=slide_text,
            slide_part_hashes=slide_hashes,
            has_vba=any(name.endswith("vbaProject.bin") for name in names),
        )


def replace_text_in_clone(source: Path, target: Path, replacements: dict[str, str]) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(source, "r") as zin, zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if is_slide_part(item.filename):
                try:
                    root = parse_xml(data)
                    changed = False
                    for node in root.xpath(".//a:t", namespaces=NS):
                        if node.text in replacements:
                            node.text = replacements[node.text]
                            changed = True
                    if changed:
                        data = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
                except etree.XMLSyntaxError:
                    pass
            zout.writestr(item, data)


def metrics_to_dict(metrics: PptxMetrics) -> dict[str, Any]:
    return asdict(metrics)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")

