from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "packages" / "pptx"))

from auditflow_pptx import duplicate_slide_in_clone, validate_pptx_package


def test_validate_pptx_package_accepts_fixture() -> None:
    source = ROOT / "tools" / "pptx-spike" / "fixtures" / "prior_year_audit_committee.pptx"
    if not source.exists():
        raise AssertionError("Run tools/pptx-spike/scripts/run_spike.py to generate the PPTX fixture.")

    report = validate_pptx_package(source)

    assert report.valid
    assert report.relationship_count > 0
    assert report.editable_text_run_count > 0
    assert report.chart_count == 1
    assert report.table_count == 1


def test_validate_pptx_package_accepts_duplicated_slide_output(tmp_path: Path) -> None:
    source = ROOT / "tools" / "pptx-spike" / "fixtures" / "prior_year_audit_committee.pptx"
    local_source = tmp_path / "source.pptx"
    target = tmp_path / "duplicated.pptx"
    shutil.copyfile(source, local_source)
    duplicate_slide_in_clone(local_source, target, slide_index=2)

    report = validate_pptx_package(target)

    assert report.valid, report.to_dict()
    assert report.chart_count == 2
    assert report.table_count == 2

