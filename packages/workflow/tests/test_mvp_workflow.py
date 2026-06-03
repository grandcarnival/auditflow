from __future__ import annotations

import sys
from pathlib import Path

from openpyxl import Workbook

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "packages" / "ai"))
sys.path.insert(0, str(ROOT / "packages" / "documents"))
sys.path.insert(0, str(ROOT / "packages" / "pptx"))
sys.path.insert(0, str(ROOT / "packages" / "workflow"))
sys.path.insert(0, str(ROOT / "tools" / "pptx-spike" / "scripts"))

from auditflow_workflow import run_mvp_workflow
from create_fixture import create_fixture


def test_run_mvp_workflow_generates_valid_preserved_export(tmp_path: Path) -> None:
    prior = tmp_path / "prior.pptx"
    findings = tmp_path / "findings.xlsx"
    output = tmp_path / "export.pptx"
    report = tmp_path / "report.json"
    manifest = tmp_path / "manifest.json"
    create_fixture(prior)
    _create_findings(findings)

    result = run_mvp_workflow(
        prior_deck=prior,
        findings_workbook=findings,
        output_deck=output,
        fiscal_year=2026,
        report_path=report,
        manifest_path=manifest,
    )

    assert output.exists()
    assert report.exists()
    assert manifest.exists()
    assert result.package_valid
    assert result.preservation_score == 1.0
    assert result.findings_count == 2
    assert result.duplicated_slides == 1
    assert len(result.summary["export_slide_text"]) == 4
    assert "Privileged access reviews lacked complete approval evidence." in result.summary["export_slide_text"][2]
    assert "Vendor access review evidence was inconsistently retained." in result.summary["export_slide_text"][3]
    assert result.manifest["manifest_version"]
    assert result.manifest["source_deck"]["sha256"]
    assert result.manifest["findings_workbook"]["details"]["workbook"]["sheet_count"] == 1
    assert result.manifest["slides_duplicated"]
    assert result.manifest["tables_updated"]
    assert result.manifest["charts_updated"]
    assert result.manifest["preservation_benchmark_results"]["score"] == 1.0


def _create_findings(path: Path) -> None:
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
    wb.save(path)
