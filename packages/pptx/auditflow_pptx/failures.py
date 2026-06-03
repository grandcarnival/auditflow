from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Any

from lxml import etree
from openpyxl import load_workbook

from .openxml import NS, read_package
from .validation import validate_pptx_package


SUPPORTED_CHART_TAGS = {
    "barChart",
    "lineChart",
    "pieChart",
}


@dataclass(frozen=True)
class FailureDiagnostic:
    failure_type: str
    severity: str
    part: str | None
    message: str
    action: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "failure_type": self.failure_type,
            "severity": self.severity,
            "part": self.part,
            "message": self.message,
            "action": self.action,
        }


def analyze_failure_modes(path: str | Path) -> list[FailureDiagnostic]:
    diagnostics: list[FailureDiagnostic] = []
    validation = validate_pptx_package(path)
    for issue in validation.issues:
        diagnostics.append(_from_validation_issue(issue.to_dict()))

    try:
        _, parts = read_package(path)
    except Exception as error:
        return diagnostics + [
            FailureDiagnostic(
                failure_type="malformed_template",
                severity="critical",
                part=None,
                message=f"Unable to read PPTX package: {error}",
                action="Ask the user to re-save the deck in Microsoft PowerPoint and upload the repaired PPTX.",
            )
        ]

    diagnostics.extend(_detect_smartart(parts))
    diagnostics.extend(_detect_unsupported_charts(parts))
    diagnostics.extend(_detect_corrupted_embedded_workbooks(parts))
    diagnostics.extend(_detect_malformed_xml(parts))
    return diagnostics


def _from_validation_issue(issue: dict[str, Any]) -> FailureDiagnostic:
    code = issue["code"]
    if code == "missing_relationship_part":
        return FailureDiagnostic(
            failure_type="missing_asset",
            severity="critical",
            part=issue.get("part"),
            message=issue["message"],
            action="Repair the source deck or remove the broken linked object before regeneration.",
        )
    if code == "bad_zip":
        return FailureDiagnostic(
            failure_type="malformed_template",
            severity="critical",
            part=issue.get("part"),
            message=issue["message"],
            action="Re-save or repair the PPTX before processing.",
        )
    return FailureDiagnostic(
        failure_type="broken_relationship" if "relationship" in code else "export_integrity",
        severity="high",
        part=issue.get("part"),
        message=issue["message"],
        action="Inspect the referenced package part and repair the deck before processing.",
    )


def _detect_smartart(parts: dict[str, bytes]) -> list[FailureDiagnostic]:
    if not any(name.startswith("ppt/diagrams/") for name in parts):
        return []
    return [
        FailureDiagnostic(
            failure_type="unsupported_smartart",
            severity="medium",
            part="ppt/diagrams",
            message="SmartArt diagram parts were detected. Current MVP does not mutate SmartArt.",
            action="Preserve SmartArt as-is; avoid mapping generated content into SmartArt until SmartArt support is implemented.",
        )
    ]


def _detect_unsupported_charts(parts: dict[str, bytes]) -> list[FailureDiagnostic]:
    diagnostics: list[FailureDiagnostic] = []
    for name, data in parts.items():
        if not name.startswith("ppt/charts/chart") or not name.endswith(".xml"):
            continue
        try:
            root = etree.fromstring(data)
        except etree.XMLSyntaxError:
            continue
        plot_area = root.find(".//c:plotArea", namespaces=NS)
        if plot_area is None:
            continue
        for child in plot_area:
            local = etree.QName(child).localname
            if local.endswith("Chart") and local not in SUPPORTED_CHART_TAGS:
                diagnostics.append(
                    FailureDiagnostic(
                        failure_type="unsupported_chart",
                        severity="medium",
                        part=name,
                        message=f"Unsupported chart type detected: {local}.",
                        action="Preserve the chart formatting but require a renderer spike before updating this chart type.",
                    )
                )
    return diagnostics


def _detect_corrupted_embedded_workbooks(parts: dict[str, bytes]) -> list[FailureDiagnostic]:
    diagnostics: list[FailureDiagnostic] = []
    for name, data in parts.items():
        if not name.startswith("ppt/embeddings/") or not name.endswith(".xlsx"):
            continue
        try:
            load_workbook(BytesIO(data), read_only=True, data_only=True)
        except Exception as error:
            diagnostics.append(
                FailureDiagnostic(
                    failure_type="corrupted_embedded_workbook",
                    severity="high",
                    part=name,
                    message=f"Embedded workbook could not be opened: {error}",
                    action="Recreate or repair the chart's embedded workbook before allowing chart data updates.",
                )
            )
    return diagnostics


def _detect_malformed_xml(parts: dict[str, bytes]) -> list[FailureDiagnostic]:
    diagnostics: list[FailureDiagnostic] = []
    for name, data in parts.items():
        if not name.endswith(".xml"):
            continue
        try:
            etree.fromstring(data)
        except etree.XMLSyntaxError as error:
            diagnostics.append(
                FailureDiagnostic(
                    failure_type="malformed_template",
                    severity="critical",
                    part=name,
                    message=f"Malformed XML part: {error}",
                    action="Repair the PPTX package before processing.",
                )
            )
    return diagnostics

