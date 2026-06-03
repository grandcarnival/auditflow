from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

from create_fixture import create_fixture
from openxml_tools import collect_metrics, metrics_to_dict, replace_text_in_clone, write_json
from python_pptx_roundtrip import roundtrip


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
FIXTURES = ROOT / "fixtures"
OUT = ROOT / "out"
PYTHON = Path(sys.executable)
NODE = Path(r"C:\Users\alexh\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe")
NODE_MODULES = Path(r"C:\Users\alexh\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\node_modules")


def node_path() -> str:
    paths = [NODE_MODULES]
    pnpm = NODE_MODULES / ".pnpm"
    if pnpm.exists():
        paths.extend(sorted(path / "node_modules" for path in pnpm.iterdir() if (path / "node_modules").exists()))
    return os.pathsep.join(str(path) for path in paths)


def timed(label: str, fn):
    start = time.perf_counter()
    value = fn()
    return value, round((time.perf_counter() - start) * 1000, 2)


def score_preservation(source: dict, target: dict) -> dict:
    checks = {
        "slide_count": source["slide_count"] == target["slide_count"],
        "masters_at_least_source": target["slide_master_count"] >= source["slide_master_count"],
        "layouts_at_least_source": target["slide_layout_count"] >= source["slide_layout_count"],
        "themes_at_least_source": target["theme_count"] >= source["theme_count"],
        "notes_at_least_source": target["notes_count"] >= source["notes_count"],
        "charts_at_least_source": target["chart_count"] >= source["chart_count"],
        "tables_at_least_source": target["table_count"] >= source["table_count"],
        "editable_text_present": target["editable_text_run_count"] > 0,
    }
    return {
        "checks": checks,
        "passed": sum(1 for passed in checks.values() if passed),
        "total": len(checks),
        "score": round(sum(1 for passed in checks.values() if passed) / len(checks), 3),
    }


def run_pptxgenjs(target: Path) -> dict:
    env = os.environ.copy()
    env["NODE_PATH"] = node_path()
    subprocess.run(
        [str(NODE), str(ROOT / "scripts" / "pptxgenjs_regenerate.cjs"), str(target)],
        check=True,
        cwd=str(REPO),
        env=env,
        capture_output=True,
        text=True,
    )
    return {"target": str(target)}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    fixture = FIXTURES / "prior_year_audit_committee.pptx"
    python_out = OUT / "python_pptx_roundtrip.pptx"
    pptxgen_out = OUT / "pptxgenjs_regenerated.pptx"
    hybrid_out = OUT / "hybrid_openxml_clone_edit.pptx"

    _, fixture_ms = timed("fixture", lambda: create_fixture(fixture))
    source_metrics = metrics_to_dict(collect_metrics(fixture))

    extraction, python_ms = timed("python-pptx", lambda: roundtrip(fixture, python_out))
    python_metrics = metrics_to_dict(collect_metrics(python_out))

    _, pptxgen_ms = timed("pptxgenjs", lambda: run_pptxgenjs(pptxgen_out))
    pptxgen_metrics = metrics_to_dict(collect_metrics(pptxgen_out))

    _, hybrid_ms = timed(
        "hybrid",
        lambda: replace_text_in_clone(
            fixture,
            hybrid_out,
            {
                "FY2025 Audit Committee": "FY2026 Audit Committee",
                "Three high-priority findings remain open.": "Two high-priority findings remain open.",
            },
        ),
    )
    hybrid_metrics = metrics_to_dict(collect_metrics(hybrid_out))

    report = {
        "environment": {
            "python": str(PYTHON),
            "node": str(NODE),
            "node_modules": str(NODE_MODULES),
        },
        "timings_ms": {
            "fixture_generation": fixture_ms,
            "python_pptx_roundtrip": python_ms,
            "pptxgenjs_regeneration": pptxgen_ms,
            "hybrid_openxml_clone_edit": hybrid_ms,
        },
        "source": source_metrics,
        "python_pptx": {
            "metrics": python_metrics,
            "extraction": extraction,
            "preservation_score": score_preservation(source_metrics, python_metrics),
        },
        "pptxgenjs": {
            "metrics": pptxgen_metrics,
            "preservation_score": score_preservation(source_metrics, pptxgen_metrics),
        },
        "hybrid_openxml": {
            "metrics": hybrid_metrics,
            "preservation_score": score_preservation(source_metrics, hybrid_metrics),
        },
    }

    write_json(OUT / "benchmark-results.json", report)
    (OUT / "benchmark-summary.md").write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps({
        "benchmark_results": str(OUT / "benchmark-results.json"),
        "benchmark_summary": str(OUT / "benchmark-summary.md"),
        "outputs": [str(python_out), str(pptxgen_out), str(hybrid_out)],
    }, indent=2))


def render_markdown(report: dict) -> str:
    rows = []
    for name in ["python_pptx", "pptxgenjs", "hybrid_openxml"]:
        entry = report[name]
        m = entry["metrics"]
        s = entry["preservation_score"]
        rows.append(
            f"| {name} | {s['passed']}/{s['total']} ({s['score']}) | {m['slide_master_count']} | {m['slide_layout_count']} | {m['theme_count']} | {m['notes_count']} | {m['table_count']} | {m['chart_count']} | {m['editable_text_run_count']} |"
        )

    return "\n".join([
        "# PowerPoint Preservation Benchmark Results",
        "",
        "## Preservation Matrix",
        "",
        "| Approach | Score | Masters | Layouts | Themes | Notes | Tables | Charts | Editable Text Runs |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        *rows,
        "",
        "## Timing",
        "",
        f"- Fixture generation: {report['timings_ms']['fixture_generation']} ms",
        f"- python-pptx round-trip: {report['timings_ms']['python_pptx_roundtrip']} ms",
        f"- pptxgenjs regeneration: {report['timings_ms']['pptxgenjs_regeneration']} ms",
        f"- Hybrid Open XML clone/edit: {report['timings_ms']['hybrid_openxml_clone_edit']} ms",
        "",
        "## Initial Interpretation",
        "",
        "- `pptxgenjs` is strong for creating editable new slides, tables, and charts, but it does not parse and preserve an existing prior-year deck as a source template.",
        "- `python-pptx` can inspect slide structure and mutate editable text, but round-tripping can drop or rewrite unsupported package parts such as manually injected notes relationships and is not ideal as the fidelity-preserving core.",
        "- Hybrid Open XML clone/edit preserves the package best because it starts from the original deck and changes only targeted XML nodes. It should be the foundation for template preservation, with a higher-level renderer used for new editable elements when needed.",
        "",
    ])


if __name__ == "__main__":
    main()
