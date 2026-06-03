from __future__ import annotations

import json
import shutil
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from auditflow_ai import build_mvp_content_map
from auditflow_documents import FindingRecord, ingest_findings_workbook
from auditflow_pptx import (
    ChartSeries,
    analyze_template,
    duplicate_slide_in_clone,
    extract_chart_data,
    extract_table_matrix,
    extract_slide_text,
    replace_text_in_clone,
    update_chart_in_clone,
    update_table_in_clone,
    validate_pptx_package,
    validate_preservation,
)
from .manifest import (
    MANIFEST_VERSION,
    OperationManifest,
    OperationRecord,
    build_preservation_benchmark_snapshot,
    file_metadata,
    utc_now,
)


@dataclass(frozen=True)
class MvpWorkflowResult:
    output_deck: str
    findings_count: int
    duplicated_slides: int
    preservation_score: float
    package_valid: bool
    manifest: dict[str, Any]
    summary: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def run_mvp_workflow(
    prior_deck: str | Path,
    findings_workbook: str | Path,
    output_deck: str | Path,
    fiscal_year: int,
    report_path: str | Path | None = None,
    manifest_path: str | Path | None = None,
) -> MvpWorkflowResult:
    prior_path = Path(prior_deck)
    output_path = Path(output_deck)
    findings = ingest_findings_workbook(findings_workbook)
    template = analyze_template(prior_path)
    content_map = build_mvp_content_map(fiscal_year=fiscal_year, findings=findings)
    if content_map.blocked:
        raise ValueError("Content map confidence is too low to generate an export.")

    operations: list[OperationRecord] = [
        OperationRecord(
            operation_type="text_replacement",
            target="all_slides",
            details=operation.to_dict(),
            confidence=operation.confidence,
            fallback_used=False,
        )
        for operation in content_map.replacements
    ]
    duplicated_records: list[dict[str, Any]] = []

    with tempfile.TemporaryDirectory() as temp_dir:
        temp = Path(temp_dir)
        text_export = temp / "step_1_text.pptx"
        table_export = temp / "step_2_table.pptx"
        chart_export = temp / "step_3_chart.pptx"
        current_export = temp / "step_4_current.pptx"

        replace_text_in_clone(
            prior_path,
            text_export,
            {operation.source_text: operation.target_text for operation in content_map.replacements},
        )

        table_rows, chart_categories, chart_series = _summary_data(findings)
        table_update = update_table_in_clone(
            text_export,
            table_export,
            slide_index=2,
            rows=table_rows,
            preserve_header=True,
        )
        operations.append(
            OperationRecord(
                operation_type="table_update",
                target="slide_2_table_0",
                details={
                    "rows": table_rows,
                    "result": table_update.to_dict(),
                },
                confidence=1.0,
                fallback_used=False,
            )
        )
        chart_update = update_chart_in_clone(
            table_export,
            chart_export,
            categories=chart_categories,
            series=chart_series,
        )
        operations.append(
            OperationRecord(
                operation_type="chart_update",
                target="chart_1",
                details={
                    "categories": chart_categories,
                    "series": [series.to_dict() for series in chart_series],
                    "result": chart_update.to_dict(),
                },
                confidence=1.0,
                fallback_used=False,
            )
        )

        duplicated = 0
        shutil.copyfile(chart_export, current_export)
        for index, finding in enumerate(findings[1:], start=2):
            next_export = temp / f"step_duplicate_{index}.pptx"
            duplicate = duplicate_slide_in_clone(current_export, next_export, slide_index=3)
            duplicated_records.append(duplicate.to_dict())
            operations.append(
                OperationRecord(
                    operation_type="slide_duplication",
                    target=f"slide_{duplicate.new_slide_index}",
                    details=duplicate.to_dict(),
                    confidence=1.0,
                    fallback_used=False,
                )
            )
            mapped_export = temp / f"step_duplicate_{index}_mapped.pptx"
            duplicate_replacements = {
                f"Finding Detail | {findings[0].title}": f"Finding Detail | {finding.title}",
                _finding_body(findings[0]): _finding_body(finding),
            }
            replace_text_in_clone(
                next_export,
                mapped_export,
                duplicate_replacements,
                slide_index=duplicate.new_slide_index,
            )
            operations.append(
                OperationRecord(
                    operation_type="slide_specific_text_replacement",
                    target=f"slide_{duplicate.new_slide_index}",
                    details={
                        "replacements": duplicate_replacements,
                        "finding_index": index,
                        "finding_title": finding.title,
                    },
                    confidence=1.0,
                    fallback_used=False,
                )
            )
            current_export = mapped_export
            duplicated += 1

        output_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(current_export, output_path)

    preservation = validate_preservation(prior_path, output_path, allow_slide_additions=True)
    package = validate_pptx_package(output_path)
    package_dict = package.to_dict()
    benchmark_snapshot = build_preservation_benchmark_snapshot(preservation, package_dict)
    manifest = OperationManifest(
        manifest_version=MANIFEST_VERSION,
        generated_at=utc_now(),
        source_deck=file_metadata(prior_path, "pptx"),
        findings_workbook=file_metadata(findings_workbook, "xlsx"),
        output_deck=file_metadata(output_path, "pptx"),
        slides_modified=_slides_modified(findings_count=len(findings), duplicated_count=duplicated),
        slides_duplicated=duplicated_records,
        tables_updated=[table_update.to_dict()],
        charts_updated=[chart_update.to_dict()],
        placeholders_mapped=[operation.to_dict() for operation in content_map.replacements],
        operations=operations,
        validation_results={
            "preservation": preservation,
            "package_validation": package_dict,
        },
        preservation_benchmark_results=benchmark_snapshot,
        warnings=content_map.warnings,
        fallback_behavior_used=[],
    )
    manifest_dict = manifest.to_dict()
    summary = {
        "template": template.to_dict(),
        "findings": [finding.to_dict() for finding in findings],
        "content_map": content_map.to_dict(),
        "table_update": table_update.to_dict(),
        "chart_update": chart_update.to_dict(),
        "preservation": preservation,
        "package_validation": package_dict,
        "manifest": manifest_dict,
        "export_table": extract_table_matrix(output_path, slide_index=2),
        "export_chart": extract_chart_data(output_path),
        "export_slide_text": extract_slide_text(output_path),
    }
    if report_path:
        Path(report_path).write_text(json.dumps(summary, indent=2), encoding="utf-8")
    if manifest_path:
        Path(manifest_path).write_text(json.dumps(manifest_dict, indent=2), encoding="utf-8")
    return MvpWorkflowResult(
        output_deck=str(output_path),
        findings_count=len(findings),
        duplicated_slides=duplicated,
        preservation_score=preservation["score"],
        package_valid=package.valid,
        manifest=manifest_dict,
        summary=summary,
    )


def _summary_data(findings: list[FindingRecord]) -> tuple[list[list[Any]], list[str], list[ChartSeries]]:
    risks = ["High", "Medium", "Low"]
    table_rows = []
    open_values = []
    closed_values = []
    for risk in risks:
        open_count = sum(1 for finding in findings if finding.risk_rating == risk and finding.status != "Closed")
        closed_count = sum(1 for finding in findings if finding.risk_rating == risk and finding.status == "Closed")
        table_rows.append([risk, open_count, closed_count])
        open_values.append(open_count)
        closed_values.append(closed_count)
    return table_rows, risks, [ChartSeries("Open", open_values), ChartSeries("Closed", closed_values)]


def _finding_body(finding: FindingRecord) -> str:
    return "\n".join([
        f"Condition: {finding.condition or 'Not provided.'}",
        f"Risk: {finding.risk_rating or 'Not rated.'}",
        f"Recommendation: {finding.recommendation or 'Not provided.'}",
    ])


def _slides_modified(findings_count: int, duplicated_count: int) -> list[int]:
    base = [1, 2, 3]
    return base + list(range(4, 4 + duplicated_count)) if findings_count else base
