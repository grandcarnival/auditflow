from __future__ import annotations

import sys
from pathlib import Path

from openpyxl import Workbook

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "packages" / "documents"))

from auditflow_documents import ingest_findings_workbook


def test_ingest_findings_workbook_maps_common_columns(tmp_path: Path) -> None:
    workbook_path = tmp_path / "findings.xlsx"
    wb = Workbook()
    ws = wb.active
    ws.title = "Findings"
    ws.append(["Finding Title", "Risk Rating", "Condition", "Recommendation", "Owner", "Due Date", "Status"])
    ws.append([
        "Access Governance",
        "High",
        "Access reviews were not consistently evidenced.",
        "Standardize evidence capture.",
        "IT",
        "2026-09-30",
        "Open",
    ])
    wb.save(workbook_path)

    findings = ingest_findings_workbook(workbook_path)

    assert len(findings) == 1
    assert findings[0].title == "Access Governance"
    assert findings[0].risk_rating == "High"
    assert findings[0].source_sheet == "Findings"

