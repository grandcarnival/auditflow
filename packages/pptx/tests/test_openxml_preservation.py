from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "packages" / "pptx"))

from auditflow_pptx import extract_slide_text, replace_text_in_clone, validate_preservation


def test_text_replacement_preserves_package_parts(tmp_path: Path) -> None:
    source = ROOT / "tools" / "pptx-spike" / "fixtures" / "prior_year_audit_committee.pptx"
    if not source.exists():
        raise AssertionError("Run tools/pptx-spike/scripts/run_spike.py to generate the PPTX fixture.")

    local_source = tmp_path / "source.pptx"
    target = tmp_path / "target.pptx"
    shutil.copyfile(source, local_source)

    replace_text_in_clone(
        local_source,
        target,
        {
            "FY2025 Audit Committee": "FY2026 Audit Committee",
            "Three high-priority findings remain open.": "Two high-priority findings remain open.",
        },
    )

    validation = validate_preservation(local_source, target)
    assert validation["score"] == 1.0
    assert "FY2026 Audit Committee" in extract_slide_text(target)[0]
    assert "Two high-priority findings remain open." in extract_slide_text(target)[1]

