from __future__ import annotations

import shutil
import sys
import zipfile
from pathlib import Path

from pptx import Presentation
from pptx.chart.data import XyChartData
from pptx.enum.chart import XL_CHART_TYPE
from pptx.util import Inches

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "packages" / "pptx"))

from auditflow_pptx import analyze_failure_modes


def test_failure_analysis_detects_missing_relationship_target(tmp_path: Path) -> None:
    source = ROOT / "tools" / "pptx-spike" / "fixtures" / "prior_year_audit_committee.pptx"
    broken = tmp_path / "broken_relationship.pptx"
    _rewrite_part(
        source,
        broken,
        "ppt/slides/_rels/slide2.xml.rels",
        lambda text: text.replace("../charts/chart1.xml", "../charts/missing-chart.xml"),
    )

    diagnostics = analyze_failure_modes(broken)

    assert any(item.failure_type == "missing_asset" for item in diagnostics)


def test_failure_analysis_detects_corrupted_embedded_workbook(tmp_path: Path) -> None:
    source = ROOT / "tools" / "pptx-spike" / "fixtures" / "prior_year_audit_committee.pptx"
    broken = tmp_path / "corrupted_workbook.pptx"
    _rewrite_binary_part(
        source,
        broken,
        "ppt/embeddings/Microsoft_Excel_Sheet1.xlsx",
        b"not an xlsx",
    )

    diagnostics = analyze_failure_modes(broken)

    assert any(item.failure_type == "corrupted_embedded_workbook" for item in diagnostics)


def test_failure_analysis_detects_unsupported_chart_type(tmp_path: Path) -> None:
    source = tmp_path / "scatter.pptx"
    _create_scatter_chart(source)

    diagnostics = analyze_failure_modes(source)

    assert any(item.failure_type == "unsupported_chart" for item in diagnostics)


def _rewrite_part(source: Path, target: Path, part_name: str, replace):
    with zipfile.ZipFile(source, "r") as zin, zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == part_name:
                data = replace(data.decode("utf-8")).encode("utf-8")
            zout.writestr(item, data)


def _rewrite_binary_part(source: Path, target: Path, part_name: str, data: bytes):
    with zipfile.ZipFile(source, "r") as zin, zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            zout.writestr(item, data if item.filename == part_name else zin.read(item.filename))


def _create_scatter_chart(path: Path) -> None:
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[5])
    slide.shapes.title.text = "Unsupported Chart"
    chart_data = XyChartData()
    series = chart_data.add_series("Scatter")
    series.add_data_point(1, 2)
    series.add_data_point(2, 3)
    slide.shapes.add_chart(XL_CHART_TYPE.XY_SCATTER_LINES, Inches(1), Inches(1.5), Inches(6), Inches(4), chart_data)
    prs.save(path)

