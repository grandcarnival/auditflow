from __future__ import annotations

import copy
import posixpath
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from lxml import etree

from .openxml import NS, REL_NS, read_package, serialize_xml, write_package


REL_TYPE_BASE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
CONTENT_TYPES_NS = "http://schemas.openxmlformats.org/package/2006/content-types"


@dataclass(frozen=True)
class SlideDuplicationResult:
    source_slide_index: int
    new_slide_index: int
    new_slide_id: int
    new_slide_part: str
    copied_parts: list[str]
    notes_preserved: bool
    chart_parts_copied: int
    embedded_parts_copied: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_slide_index": self.source_slide_index,
            "new_slide_index": self.new_slide_index,
            "new_slide_id": self.new_slide_id,
            "new_slide_part": self.new_slide_part,
            "copied_parts": self.copied_parts,
            "notes_preserved": self.notes_preserved,
            "chart_parts_copied": self.chart_parts_copied,
            "embedded_parts_copied": self.embedded_parts_copied,
        }


def duplicate_slide_in_clone(
    source: str | Path,
    target: str | Path,
    slide_index: int,
) -> SlideDuplicationResult:
    infos, parts = read_package(source)
    source_slide = f"ppt/slides/slide{slide_index}.xml"
    if source_slide not in parts:
        raise ValueError(f"Slide {slide_index} was not found.")

    existing_slide_indices = _existing_indices(parts, r"ppt/slides/slide(\d+)\.xml")
    new_slide_index = max(existing_slide_indices) + 1
    new_slide = f"ppt/slides/slide{new_slide_index}.xml"
    new_slide_rels = f"ppt/slides/_rels/slide{new_slide_index}.xml.rels"
    source_slide_rels = f"ppt/slides/_rels/slide{slide_index}.xml.rels"

    copied_parts = [new_slide]
    parts[new_slide] = parts[source_slide]

    rels_root = etree.fromstring(parts[source_slide_rels]) if source_slide_rels in parts else _empty_relationships()
    new_rels_root = copy.deepcopy(rels_root)
    chart_parts = 0
    embedded_parts = 0
    notes_preserved = False

    for rel in new_rels_root:
        rel_type = rel.get("Type", "")
        target_ref = rel.get("Target", "")
        if rel_type.endswith("/chart"):
            old_part = _resolve_part(source_slide_rels, target_ref)
            new_part = _copy_numbered_part(parts, old_part, "ppt/charts/chart", ".xml")
            rel.set("Target", _relative_target(new_slide_rels, new_part))
            copied_parts.append(new_part)
            chart_parts += 1
            old_chart_rels = _rels_name(old_part)
            if old_chart_rels in parts:
                new_chart_rels = _rels_name(new_part)
                chart_rels_root = copy.deepcopy(etree.fromstring(parts[old_chart_rels]))
                for chart_rel in chart_rels_root:
                    if chart_rel.get("Type", "").endswith("/package"):
                        old_embedded = _resolve_part(old_chart_rels, chart_rel.get("Target", ""))
                        new_embedded = _copy_numbered_part(
                            parts,
                            old_embedded,
                            "ppt/embeddings/Microsoft_Excel_Sheet",
                            ".xlsx",
                        )
                        chart_rel.set("Target", _relative_target(new_chart_rels, new_embedded))
                        copied_parts.append(new_embedded)
                        embedded_parts += 1
                parts[new_chart_rels] = serialize_xml(chart_rels_root)
                copied_parts.append(new_chart_rels)
        elif rel_type.endswith("/notesSlide"):
            old_part = _resolve_part(source_slide_rels, target_ref)
            new_part = _copy_numbered_part(parts, old_part, "ppt/notesSlides/notesSlide", ".xml")
            rel.set("Target", _relative_target(new_slide_rels, new_part))
            copied_parts.append(new_part)
            notes_preserved = True
            old_notes_rels = _rels_name(old_part)
            if old_notes_rels in parts:
                new_notes_rels = _rels_name(new_part)
                notes_rels_root = copy.deepcopy(etree.fromstring(parts[old_notes_rels]))
                for note_rel in notes_rels_root:
                    if note_rel.get("Type", "").endswith("/slide"):
                        note_rel.set("Target", _relative_target(new_notes_rels, new_slide))
                parts[new_notes_rels] = serialize_xml(notes_rels_root)
                copied_parts.append(new_notes_rels)
    parts[new_slide_rels] = serialize_xml(new_rels_root)
    copied_parts.append(new_slide_rels)

    new_slide_id = _append_slide_to_presentation(parts, new_slide_index)
    _ensure_content_type(parts, f"/{new_slide}", "application/vnd.openxmlformats-officedocument.presentationml.slide+xml")
    for part in copied_parts:
        if part.startswith("ppt/charts/") and part.endswith(".xml"):
            _ensure_content_type(parts, f"/{part}", "application/vnd.openxmlformats-officedocument.drawingml.chart+xml")
        if part.startswith("ppt/notesSlides/") and part.endswith(".xml"):
            _ensure_content_type(parts, f"/{part}", "application/vnd.openxmlformats-officedocument.presentationml.notesSlide+xml")

    write_package(target, infos, parts)
    return SlideDuplicationResult(
        source_slide_index=slide_index,
        new_slide_index=new_slide_index,
        new_slide_id=new_slide_id,
        new_slide_part=new_slide,
        copied_parts=sorted(copied_parts),
        notes_preserved=notes_preserved,
        chart_parts_copied=chart_parts,
        embedded_parts_copied=embedded_parts,
    )


def _append_slide_to_presentation(parts: dict[str, bytes], new_slide_index: int) -> int:
    presentation = etree.fromstring(parts["ppt/presentation.xml"])
    rels = etree.fromstring(parts["ppt/_rels/presentation.xml.rels"])
    rel_ids = [_rel_number(rel.get("Id", "")) for rel in rels]
    next_rel_id = max([value for value in rel_ids if value is not None], default=0) + 1
    rel_id = f"rId{next_rel_id}"
    rel = etree.SubElement(rels, f"{{{REL_NS}}}Relationship")
    rel.set("Id", rel_id)
    rel.set("Type", f"{REL_TYPE_BASE}/slide")
    rel.set("Target", f"slides/slide{new_slide_index}.xml")

    slide_id_list = presentation.find("p:sldIdLst", namespaces=NS)
    if slide_id_list is None:
        slide_id_list = etree.SubElement(presentation, f"{{{NS['p']}}}sldIdLst")
    existing_ids = [
        int(node.get("id"))
        for node in slide_id_list.findall("p:sldId", namespaces=NS)
        if node.get("id")
    ]
    new_slide_id = max(existing_ids, default=255) + 1
    slide_id = etree.SubElement(slide_id_list, f"{{{NS['p']}}}sldId")
    slide_id.set("id", str(new_slide_id))
    slide_id.set(f"{{{NS['r']}}}id", rel_id)

    parts["ppt/presentation.xml"] = serialize_xml(presentation)
    parts["ppt/_rels/presentation.xml.rels"] = serialize_xml(rels)
    return new_slide_id


def _ensure_content_type(parts: dict[str, bytes], part_name: str, content_type: str) -> None:
    root = etree.fromstring(parts["[Content_Types].xml"])
    for override in root.findall(f"{{{CONTENT_TYPES_NS}}}Override"):
        if override.get("PartName") == part_name:
            return
    override = etree.SubElement(root, f"{{{CONTENT_TYPES_NS}}}Override")
    override.set("PartName", part_name)
    override.set("ContentType", content_type)
    parts["[Content_Types].xml"] = serialize_xml(root)


def _copy_numbered_part(parts: dict[str, bytes], old_part: str, prefix: str, suffix: str) -> str:
    indices = _existing_indices(parts, re.escape(prefix) + r"(\d+)" + re.escape(suffix))
    new_part = f"{prefix}{max(indices, default=0) + 1}{suffix}"
    parts[new_part] = parts[old_part]
    return new_part


def _existing_indices(parts: dict[str, bytes], pattern: str) -> list[int]:
    values = []
    compiled = re.compile(pattern)
    for name in parts:
        match = compiled.fullmatch(name)
        if match:
            values.append(int(match.group(1)))
    return values


def _resolve_part(source_rels_name: str, target: str) -> str:
    owner_part = source_rels_name.replace("_rels/", "").removesuffix(".rels")
    base_dir = posixpath.dirname(owner_part)
    return posixpath.normpath(posixpath.join(base_dir, target))


def _relative_target(source_rels_name: str, target_part: str) -> str:
    owner_part = source_rels_name.replace("_rels/", "").removesuffix(".rels")
    base_dir = posixpath.dirname(owner_part)
    return posixpath.relpath(target_part, base_dir)


def _rels_name(part_name: str) -> str:
    directory = posixpath.dirname(part_name)
    filename = posixpath.basename(part_name)
    return f"{directory}/_rels/{filename}.rels"


def _empty_relationships() -> etree._Element:
    return etree.Element(f"{{{REL_NS}}}Relationships")


def _rel_number(rel_id: str) -> int | None:
    match = re.fullmatch(r"rId(\d+)", rel_id)
    return int(match.group(1)) if match else None

