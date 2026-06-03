from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "packages" / "pptx"))
sys.path.insert(0, str(ROOT / "tools" / "pptx-spike" / "scripts"))

from auditflow_pptx import (  # noqa: E402
    ChartSeries,
    collect_metrics,
    duplicate_slide_in_clone,
    replace_text_in_clone,
    update_chart_in_clone,
    update_table_in_clone,
    validate_pptx_package,
    validate_preservation,
)
from create_fixture import create_fixture  # noqa: E402


OUT = ROOT / "tools" / "preservation-benchmark" / "out"
SOURCE = ROOT / "tools" / "pptx-spike" / "fixtures" / "prior_year_audit_committee.pptx"


@dataclass(frozen=True)
class BenchmarkCase:
    name: str
    output: Path
    allow_slide_additions: bool = False


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    create_fixture(SOURCE)
    cases = build_cases()
    results = [score_case(case) for case in cases]
    suite_score = round(sum(item["score"] for item in results) / len(results), 3)
    report = {
        "suite_score": suite_score,
        "case_count": len(results),
        "source": str(SOURCE),
        "results": results,
    }
    (OUT / "preservation-benchmark-results.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (OUT / "preservation-benchmark-summary.md").write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps({
        "suite_score": suite_score,
        "case_count": len(results),
        "results": str(OUT / "preservation-benchmark-results.json"),
        "summary": str(OUT / "preservation-benchmark-summary.md"),
    }, indent=2))


def build_cases() -> list[BenchmarkCase]:
    text_out = OUT / "case_text_replacement.pptx"
    table_out = OUT / "case_table_update.pptx"
    chart_out = OUT / "case_chart_update.pptx"
    duplicate_out = OUT / "case_slide_duplication.pptx"

    replace_text_in_clone(
        SOURCE,
        text_out,
        {
            "FY2025 Audit Committee": "FY2026 Audit Committee",
            "Three high-priority findings remain open.": "One high-priority finding remains open.",
        },
    )
    update_table_in_clone(
        text_out,
        table_out,
        slide_index=2,
        preserve_header=True,
        rows=[
            ["High", 1, 0],
            ["Medium", 1, 0],
            ["Low", 0, 1],
        ],
    )
    update_chart_in_clone(
        table_out,
        chart_out,
        categories=["High", "Medium", "Low"],
        series=[
            ChartSeries("Open", [1, 1, 0]),
            ChartSeries("Closed", [0, 0, 1]),
        ],
    )
    duplicate_slide_in_clone(chart_out, duplicate_out, slide_index=3)

    return [
        BenchmarkCase("text_replacement", text_out),
        BenchmarkCase("table_update", table_out),
        BenchmarkCase("chart_update", chart_out),
        BenchmarkCase("slide_duplication", duplicate_out, allow_slide_additions=True),
    ]


def score_case(case: BenchmarkCase) -> dict[str, Any]:
    preservation = validate_preservation(SOURCE, case.output, allow_slide_additions=case.allow_slide_additions)
    package = validate_pptx_package(case.output)
    source_metrics = collect_metrics(SOURCE)
    output_metrics = collect_metrics(case.output)
    dimensions = {
        "layout_preservation": _score(output_metrics.slide_layout_count >= source_metrics.slide_layout_count),
        "notes_preservation": _score(output_metrics.notes_count >= source_metrics.notes_count),
        "chart_preservation": _score(output_metrics.chart_count >= source_metrics.chart_count),
        "table_preservation": _score(output_metrics.table_count >= source_metrics.table_count),
        "theme_preservation": _score(output_metrics.theme_count >= source_metrics.theme_count),
        "editability": _score(output_metrics.editable_text_run_count > 0),
        "corruption_rate": _score(package.valid),
        "export_integrity": _score(package.valid and not package.issues),
    }
    score = round(sum(dimensions.values()) / len(dimensions), 3)
    return {
        "name": case.name,
        "output": str(case.output),
        "score": score,
        "dimensions": dimensions,
        "preservation": preservation,
        "package_validation": package.to_dict(),
    }


def render_markdown(report: dict[str, Any]) -> str:
    rows = [
        f"| {item['name']} | {item['score']} | "
        f"{item['dimensions']['layout_preservation']} | "
        f"{item['dimensions']['notes_preservation']} | "
        f"{item['dimensions']['chart_preservation']} | "
        f"{item['dimensions']['table_preservation']} | "
        f"{item['dimensions']['theme_preservation']} | "
        f"{item['dimensions']['editability']} | "
        f"{item['dimensions']['corruption_rate']} | "
        f"{item['dimensions']['export_integrity']} |"
        for item in report["results"]
    ]
    return "\n".join([
        "# Preservation Fidelity Benchmark Summary",
        "",
        f"Suite score: `{report['suite_score']}`",
        "",
        "| Case | Score | Layout | Notes | Charts | Tables | Theme | Editable | Not Corrupt | Integrity |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        *rows,
        "",
    ])


def _score(value: bool) -> float:
    return 1.0 if value else 0.0


if __name__ == "__main__":
    main()

