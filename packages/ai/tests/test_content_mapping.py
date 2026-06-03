from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "packages" / "ai"))
sys.path.insert(0, str(ROOT / "packages" / "documents"))
sys.path.insert(0, str(ROOT / "packages" / "pptx"))

from auditflow_ai import build_mvp_content_map
from auditflow_documents import FindingRecord
from auditflow_pptx import extract_slide_text, replace_text_in_clone, validate_preservation


def test_content_map_can_regenerate_fixture_deck(tmp_path: Path) -> None:
    source = ROOT / "tools" / "pptx-spike" / "fixtures" / "prior_year_audit_committee.pptx"
    if not source.exists():
        raise AssertionError("Run tools/pptx-spike/scripts/run_spike.py to generate the PPTX fixture.")

    local_source = tmp_path / "source.pptx"
    target = tmp_path / "mapped.pptx"
    shutil.copyfile(source, local_source)

    findings = [
        FindingRecord(
            row_number=2,
            title="Privileged Access Review",
            risk_rating="High",
            condition="Privileged access reviews lacked complete approval evidence.",
            recommendation="Require quarterly evidence capture and exception escalation.",
            owner="IT",
            due_date="2026-09-30",
            status="Open",
            source_sheet="Findings",
        )
    ]

    content_map = build_mvp_content_map(fiscal_year=2026, findings=findings)
    assert not content_map.blocked
    assert content_map.confidence >= 0.95
    assert all(operation.source_fields for operation in content_map.replacements)
    replace_text_in_clone(
        local_source,
        target,
        {operation.source_text: operation.target_text for operation in content_map.replacements},
    )

    slides = extract_slide_text(target)
    validation = validate_preservation(local_source, target)

    assert validation["score"] == 1.0
    assert "FY2026 Audit Committee" in slides[0]
    assert "One high-priority finding remains open." in slides[1]
    assert "Finding Detail | Privileged Access Review" in slides[2]
    assert "Privileged access reviews lacked complete approval evidence." in slides[2]
