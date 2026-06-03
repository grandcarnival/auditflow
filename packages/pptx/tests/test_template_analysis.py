from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "packages" / "pptx"))

from auditflow_pptx import analyze_template


def test_template_analysis_extracts_slide_roles_and_structure() -> None:
    source = ROOT / "tools" / "pptx-spike" / "fixtures" / "prior_year_audit_committee.pptx"
    if not source.exists():
        raise AssertionError("Run tools/pptx-spike/scripts/run_spike.py to generate the PPTX fixture.")

    model = analyze_template(source)

    assert model.slide_count == 3
    assert model.slide_width_emu is not None
    assert model.slide_height_emu is not None
    assert [slide.role_hint for slide in model.slides] == [
        "cover",
        "executive_summary",
        "finding_detail",
    ]
    assert model.slides[1].table_count == 1
    assert model.slides[1].chart_count == 1
    assert model.slides[1].note_text is not None
    assert model.slides[1].layout_fingerprint
    assert "summary" in model.slides[1].semantic_placeholders
    assert "table" in model.slides[1].semantic_placeholders
    assert "chart" in model.slides[1].semantic_placeholders
    assert "executive summary" in model.slides[1].recurring_markers
    assert model.slides[2].is_title_content
