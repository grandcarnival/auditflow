from __future__ import annotations

import shutil
import sys
import zipfile
from io import BytesIO
from pathlib import Path

from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "packages" / "pptx"))

from auditflow_pptx import ChartSeries, extract_chart_data, update_chart_in_clone, validate_preservation


def test_chart_update_preserves_relationship_and_updates_embedded_workbook(tmp_path: Path) -> None:
    source = ROOT / "tools" / "pptx-spike" / "fixtures" / "prior_year_audit_committee.pptx"
    if not source.exists():
        raise AssertionError("Run tools/pptx-spike/scripts/run_spike.py to generate the PPTX fixture.")

    local_source = tmp_path / "source.pptx"
    target = tmp_path / "updated_chart.pptx"
    shutil.copyfile(source, local_source)

    result = update_chart_in_clone(
        local_source,
        target,
        categories=["High", "Medium", "Low"],
        series=[
            ChartSeries("Open", [2, 6, 3]),
            ChartSeries("Closed", [3, 6, 9]),
        ],
    )

    chart_data = extract_chart_data(target)
    validation = validate_preservation(local_source, target)

    assert result.embedded_workbook_updated
    assert result.series_count_preserved
    assert result.relationship_preserved
    assert chart_data == {
        "categories": ["High", "Medium", "Low"],
        "series": [
            {"name": "Open", "values": [2, 6, 3]},
            {"name": "Closed", "values": [3, 6, 9]},
        ],
    }
    assert validation["checks"]["charts_preserved"]
    assert validation["checks"]["tables_preserved"]
    assert _embedded_cell(target, "B2") == 2
    assert _embedded_cell(target, "C4") == 9


def test_chart_update_can_resize_category_cache(tmp_path: Path) -> None:
    source = ROOT / "tools" / "pptx-spike" / "fixtures" / "prior_year_audit_committee.pptx"
    local_source = tmp_path / "source.pptx"
    target = tmp_path / "updated_chart_resized.pptx"
    shutil.copyfile(source, local_source)

    update_chart_in_clone(
        local_source,
        target,
        categories=["High", "Medium", "Low", "Advisory"],
        series=[
            ChartSeries("Open", [2, 6, 3, 1]),
            ChartSeries("Closed", [3, 6, 9, 4]),
        ],
    )

    chart_data = extract_chart_data(target)
    assert chart_data["categories"] == ["High", "Medium", "Low", "Advisory"]
    assert chart_data["series"][0]["values"] == [2, 6, 3, 1]
    assert _embedded_cell(target, "A5") == "Advisory"
    assert _embedded_cell(target, "B5") == 1


def _embedded_cell(path: Path, coordinate: str):
    with zipfile.ZipFile(path) as zf:
        workbook = load_workbook(BytesIO(zf.read("ppt/embeddings/Microsoft_Excel_Sheet1.xlsx")), data_only=True)
        return workbook.active[coordinate].value

