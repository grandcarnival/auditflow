from __future__ import annotations

import shutil
import sys
from pathlib import Path

from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE
from pptx.util import Inches

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "packages" / "pptx"))

from auditflow_pptx import ChartSeries, extract_chart_data, update_chart_in_clone, validate_pptx_package


def test_chart_update_can_add_series_count(tmp_path: Path) -> None:
    source = ROOT / "tools" / "pptx-spike" / "fixtures" / "prior_year_audit_committee.pptx"
    target = tmp_path / "three_series.pptx"
    shutil.copyfile(source, target)

    update_chart_in_clone(
        target,
        target,
        categories=["High", "Medium", "Low"],
        series=[
            ChartSeries("Open", [2, 6, 3]),
            ChartSeries("Closed", [3, 6, 9]),
            ChartSeries("Deferred", [1, 2, 0]),
        ],
    )

    data = extract_chart_data(target)
    assert [series["name"] for series in data["series"]] == ["Open", "Closed", "Deferred"]
    assert data["series"][2]["values"] == [1, 2, 0]
    assert validate_pptx_package(target).valid


def test_chart_update_can_remove_series_count(tmp_path: Path) -> None:
    source = ROOT / "tools" / "pptx-spike" / "fixtures" / "prior_year_audit_committee.pptx"
    target = tmp_path / "one_series.pptx"
    shutil.copyfile(source, target)

    update_chart_in_clone(
        target,
        target,
        categories=["High", "Medium", "Low"],
        series=[ChartSeries("Open", [2, 6, 3])],
    )

    data = extract_chart_data(target)
    assert len(data["series"]) == 1
    assert data["series"][0]["name"] == "Open"
    assert validate_pptx_package(target).valid


def test_line_chart_update_preserves_chart_package(tmp_path: Path) -> None:
    source = tmp_path / "line_source.pptx"
    target = tmp_path / "line_updated.pptx"
    _create_chart_fixture(source, XL_CHART_TYPE.LINE_MARKERS, has_data_labels=True)

    update_chart_in_clone(
        source,
        target,
        categories=["Q1", "Q2", "Q3", "Q4"],
        series=[
            ChartSeries("Open", [5, 4, 3, 2]),
            ChartSeries("Closed", [1, 3, 6, 8]),
        ],
    )

    assert extract_chart_data(target)["categories"] == ["Q1", "Q2", "Q3", "Q4"]
    assert validate_pptx_package(target).valid


def test_pie_chart_update_preserves_chart_package(tmp_path: Path) -> None:
    source = tmp_path / "pie_source.pptx"
    target = tmp_path / "pie_updated.pptx"
    _create_chart_fixture(source, XL_CHART_TYPE.PIE, series_count=1, has_data_labels=True)

    update_chart_in_clone(
        source,
        target,
        categories=["High", "Medium", "Low"],
        series=[ChartSeries("Open", [2, 6, 3])],
    )

    assert extract_chart_data(target)["series"][0]["values"] == [2, 6, 3]
    assert validate_pptx_package(target).valid


def test_stacked_bar_chart_update_preserves_chart_package(tmp_path: Path) -> None:
    source = tmp_path / "stacked_source.pptx"
    target = tmp_path / "stacked_updated.pptx"
    _create_chart_fixture(source, XL_CHART_TYPE.BAR_STACKED, has_data_labels=True)

    update_chart_in_clone(
        source,
        target,
        categories=["High", "Medium", "Low"],
        series=[
            ChartSeries("Open", [2, 6, 3]),
            ChartSeries("Closed", [3, 6, 9]),
        ],
    )

    data = extract_chart_data(target)
    assert data["series"][0]["values"] == [2, 6, 3]
    assert data["series"][1]["values"] == [3, 6, 9]
    assert validate_pptx_package(target).valid


def _create_chart_fixture(
    path: Path,
    chart_type: XL_CHART_TYPE,
    series_count: int = 2,
    has_data_labels: bool = False,
) -> None:
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[5])
    slide.shapes.title.text = "Chart Fixture"
    data = CategoryChartData()
    data.categories = ["High", "Medium", "Low"]
    data.add_series("Open", (1, 2, 3))
    if series_count > 1:
        data.add_series("Closed", (3, 2, 1))
    chart = slide.shapes.add_chart(chart_type, Inches(1), Inches(1.4), Inches(7), Inches(4), data).chart
    if has_data_labels:
        chart.plots[0].has_data_labels = True
    prs.save(path)

