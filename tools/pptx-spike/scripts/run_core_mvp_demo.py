from __future__ import annotations

import json
import sys
from pathlib import Path

from openpyxl import Workbook

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "packages" / "ai"))
sys.path.insert(0, str(ROOT / "packages" / "documents"))
sys.path.insert(0, str(ROOT / "packages" / "pptx"))

from auditflow_ai import build_mvp_content_map
from auditflow_documents import ingest_findings_workbook
from auditflow_pptx import (
    ChartSeries,
    analyze_template,
    duplicate_slide_in_clone,
    extract_chart_data,
    extract_slide_text,
    extract_table_matrix,
    replace_text_in_clone,
    update_chart_in_clone,
    update_table_in_clone,
    validate_pptx_package,
    validate_preservation,
)


OUT = ROOT / "tools" / "pptx-spike" / "out"
SOURCE = ROOT / "tools" / "pptx-spike" / "fixtures" / "prior_year_audit_committee.pptx"
FINDINGS = OUT / "current_year_findings.xlsx"
EXPORT = OUT / "auditflow_core_mvp_export.pptx"
REPORT = OUT / "core-mvp-demo-report.json"


def main() -> None:
    if not SOURCE.exists():
        raise SystemExit("Run tools/pptx-spike/scripts/run_spike.py before this demo.")

    OUT.mkdir(parents=True, exist_ok=True)
    create_findings_fixture(FINDINGS)
    findings = ingest_findings_workbook(FINDINGS)
    template = analyze_template(SOURCE)
    content_map = build_mvp_content_map(fiscal_year=2026, findings=findings)

    text_export = OUT / "demo_step_1_text.pptx"
    table_export = OUT / "demo_step_2_table.pptx"
    chart_export = OUT / "demo_step_3_chart.pptx"
    duplicated_export = OUT / "demo_step_4_duplicated.pptx"

    replace_text_in_clone(
        SOURCE,
        text_export,
        {operation.source_text: operation.target_text for operation in content_map.replacements},
    )
    table_rows, chart_categories, chart_series = summary_data(findings)
    table_result = update_table_in_clone(
        text_export,
        table_export,
        slide_index=2,
        rows=table_rows,
        preserve_header=True,
    )
    chart_result = update_chart_in_clone(
        table_export,
        chart_export,
        categories=chart_categories,
        series=chart_series,
    )
    duplicate_result = duplicate_slide_in_clone(chart_export, duplicated_export, slide_index=3)
    second = findings[1] if len(findings) > 1 else None
    if second:
        replace_text_in_clone(
            duplicated_export,
            EXPORT,
            {
                f"Finding Detail | {findings[0].title}": f"Finding Detail | {second.title}",
                finding_body(findings[0]): finding_body(second),
            },
            slide_index=duplicate_result.new_slide_index,
        )
    else:
        duplicated_export.replace(EXPORT)

    validation = validate_preservation(SOURCE, EXPORT, allow_slide_additions=True)
    package_validation = validate_pptx_package(EXPORT)
    report = {
        "source_deck": str(SOURCE),
        "findings_workbook": str(FINDINGS),
        "export": str(EXPORT),
        "template": template.to_dict(),
        "findings": [finding.to_dict() for finding in findings],
        "content_map": content_map.to_dict(),
        "table_update": table_result.to_dict(),
        "chart_update": chart_result.to_dict(),
        "slide_duplication": duplicate_result.to_dict(),
        "validation": validation,
        "package_validation": package_validation.to_dict(),
        "export_table": extract_table_matrix(EXPORT, slide_index=2),
        "export_chart": extract_chart_data(EXPORT),
        "export_slide_text": extract_slide_text(EXPORT),
    }
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({
        "export": str(EXPORT),
        "report": str(REPORT),
        "preservation_score": validation["score"],
        "package_valid": package_validation.valid,
    }, indent=2))


def create_findings_fixture(path: Path) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "Findings"
    ws.append(["Finding Title", "Risk Rating", "Condition", "Recommendation", "Owner", "Due Date", "Status"])
    ws.append([
        "Privileged Access Review",
        "High",
        "Privileged access reviews lacked complete approval evidence.",
        "Require quarterly evidence capture and exception escalation.",
        "IT",
        "2026-09-30",
        "Open",
    ])
    ws.append([
        "Vendor Access Monitoring",
        "Medium",
        "Vendor access review evidence was inconsistently retained.",
        "Centralize vendor access review evidence and owner attestations.",
        "Procurement",
        "2026-10-31",
        "Open",
    ])
    ws.append([
        "Legacy User Cleanup",
        "Low",
        "Terminated users were removed after the target SLA in two cases.",
        "Automate stale-account reporting.",
        "IT",
        "2026-08-15",
        "Closed",
    ])
    wb.save(path)


def summary_data(findings):
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


def finding_body(finding) -> str:
    return "\n".join([
        f"Condition: {finding.condition or 'Not provided.'}",
        f"Risk: {finding.risk_rating or 'Not rated.'}",
        f"Recommendation: {finding.recommendation or 'Not provided.'}",
    ])


if __name__ == "__main__":
    main()
