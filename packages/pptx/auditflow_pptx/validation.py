from __future__ import annotations

import posixpath
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from lxml import etree

from .openxml import NS, REL_NS, collect_metrics, read_package


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str
    part: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {"code": self.code, "message": self.message, "part": self.part}


@dataclass(frozen=True)
class PptxValidationReport:
    valid: bool
    issues: list[ValidationIssue]
    relationship_count: int
    editable_text_run_count: int
    chart_count: int
    table_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "issues": [issue.to_dict() for issue in self.issues],
            "relationship_count": self.relationship_count,
            "editable_text_run_count": self.editable_text_run_count,
            "chart_count": self.chart_count,
            "table_count": self.table_count,
        }


def validate_pptx_package(path: str | Path) -> PptxValidationReport:
    pptx_path = Path(path)
    issues: list[ValidationIssue] = []
    relationship_count = 0

    try:
        with zipfile.ZipFile(pptx_path) as zf:
            corrupt = zf.testzip()
            if corrupt:
                issues.append(ValidationIssue("zip_corrupt_part", f"Corrupt ZIP part: {corrupt}", corrupt))
    except zipfile.BadZipFile:
        return PptxValidationReport(
            valid=False,
            issues=[ValidationIssue("bad_zip", "PPTX is not a valid ZIP package.", None)],
            relationship_count=0,
            editable_text_run_count=0,
            chart_count=0,
            table_count=0,
        )

    _, parts = read_package(pptx_path)
    content_types = _content_type_overrides(parts)

    for rels_name, rels_data in parts.items():
        if not rels_name.endswith(".rels"):
            continue
        try:
            root = etree.fromstring(rels_data)
        except etree.XMLSyntaxError as error:
            issues.append(ValidationIssue("invalid_relationship_xml", str(error), rels_name))
            continue
        for rel in root:
            relationship_count += 1
            target_mode = rel.get("TargetMode")
            if target_mode == "External":
                continue
            target = rel.get("Target")
            if not target:
                issues.append(ValidationIssue("missing_relationship_target", "Relationship has no target.", rels_name))
                continue
            resolved = _resolve_relationship_target(rels_name, target)
            if resolved not in parts:
                issues.append(
                    ValidationIssue(
                        "missing_relationship_part",
                        f"Relationship target does not exist: {target} -> {resolved}",
                        rels_name,
                    )
                )

    for part_name in parts:
        if _requires_override(part_name) and f"/{part_name}" not in content_types:
            issues.append(
                ValidationIssue(
                    "missing_content_type_override",
                    f"Part is missing content type override: /{part_name}",
                    part_name,
                )
            )

    metrics = collect_metrics(pptx_path)
    if metrics.editable_text_run_count == 0:
        issues.append(ValidationIssue("no_editable_text", "No editable text runs were found.", None))
    if metrics.slide_count == 0:
        issues.append(ValidationIssue("no_slides", "No slides were found.", None))

    return PptxValidationReport(
        valid=not issues,
        issues=issues,
        relationship_count=relationship_count,
        editable_text_run_count=metrics.editable_text_run_count,
        chart_count=metrics.chart_count,
        table_count=metrics.table_count,
    )


def _content_type_overrides(parts: dict[str, bytes]) -> set[str]:
    root = etree.fromstring(parts["[Content_Types].xml"])
    return {
        override.get("PartName", "")
        for override in root.findall("{http://schemas.openxmlformats.org/package/2006/content-types}Override")
    }


def _requires_override(part_name: str) -> bool:
    return bool(re.fullmatch(r"ppt/(slides|charts|notesSlides)/.+\.xml", part_name))


def _resolve_relationship_target(rels_name: str, target: str) -> str:
    if rels_name == "_rels/.rels":
        return posixpath.normpath(target)
    owner_part = rels_name.replace("_rels/", "").removesuffix(".rels")
    base_dir = posixpath.dirname(owner_part)
    return posixpath.normpath(posixpath.join(base_dir, target))

