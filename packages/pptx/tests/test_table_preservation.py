from __future__ import annotations

import shutil
import sys
from pathlib import Path

from pptx import Presentation
from pptx.util import Inches

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "packages" / "pptx"))

from auditflow_pptx import (
    extract_table_matrix,
    update_table_in_clone,
    validate_preservation,
)


def test_table_cell_replacement_and_row_insertion_preserves_structure(tmp_path: Path) -> None:
    source = ROOT / "tools" / "pptx-spike" / "fixtures" / "prior_year_audit_committee.pptx"
    if not source.exists():
        raise AssertionError("Run tools/pptx-spike/scripts/run_spike.py to generate the PPTX fixture.")

    local_source = tmp_path / "source.pptx"
    target = tmp_path / "updated_table.pptx"
    shutil.copyfile(source, local_source)

    result = update_table_in_clone(
        local_source,
        target,
        slide_index=2,
        preserve_header=True,
        rows=[
            ["High", 2, 3],
            ["Medium", 6, 6],
            ["Low", 3, 9],
            ["Advisory", 1, 4],
        ],
    )

    matrix = extract_table_matrix(target, slide_index=2)
    validation = validate_preservation(local_source, target)

    assert result.original_rows == 4
    assert result.updated_rows == 5
    assert result.style_preserved
    assert result.merged_cells_preserved
    assert matrix == [
        ["Risk", "Open", "Closed"],
        ["High", "2", "3"],
        ["Medium", "6", "6"],
        ["Low", "3", "9"],
        ["Advisory", "1", "4"],
    ]
    assert validation["checks"]["tables_preserved"]
    assert validation["checks"]["notes_preserved"]


def test_table_row_removal_preserves_header_and_numeric_formatting(tmp_path: Path) -> None:
    source = ROOT / "tools" / "pptx-spike" / "fixtures" / "prior_year_audit_committee.pptx"
    local_source = tmp_path / "source.pptx"
    target = tmp_path / "smaller_table.pptx"
    shutil.copyfile(source, local_source)

    update_table_in_clone(
        local_source,
        target,
        slide_index=2,
        preserve_header=True,
        rows=[
            ["High", 2.0, 3.0],
        ],
    )

    assert extract_table_matrix(target, slide_index=2) == [
        ["Risk", "Open", "Closed"],
        ["High", "2", "3"],
    ]


def test_merged_cell_structure_survives_body_row_update(tmp_path: Path) -> None:
    source = tmp_path / "merged_source.pptx"
    target = tmp_path / "merged_target.pptx"
    _create_merged_table_fixture(source)

    result = update_table_in_clone(
        source,
        target,
        slide_index=1,
        preserve_header=True,
        rows=[
            ["High", 2, 3],
            ["Medium", 6, 6],
        ],
    )

    assert result.merged_cells_preserved
    assert result.style_preserved
    assert extract_table_matrix(target, slide_index=1) == [
        ["Risk Summary", ""],
        ["High", "2"],
        ["Medium", "6"],
    ]


def _create_merged_table_fixture(path: Path) -> None:
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[5])
    slide.shapes.title.text = "Merged Table"
    table = slide.shapes.add_table(3, 2, Inches(1), Inches(1.5), Inches(5), Inches(2)).table
    table.cell(0, 0).text = "Risk Summary"
    table.cell(0, 0).merge(table.cell(0, 1))
    table.cell(1, 0).text = "High"
    table.cell(1, 1).text = "1"
    table.cell(2, 0).text = "Low"
    table.cell(2, 1).text = "4"
    prs.save(path)
