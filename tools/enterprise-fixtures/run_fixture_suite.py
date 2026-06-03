from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from openpyxl import Workbook

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "packages" / "ai"))
sys.path.insert(0, str(ROOT / "packages" / "documents"))
sys.path.insert(0, str(ROOT / "packages" / "pptx"))
sys.path.insert(0, str(ROOT / "packages" / "workflow"))
sys.path.insert(0, str(ROOT / "tools" / "pptx-spike" / "scripts"))

from auditflow_pptx import analyze_failure_modes  # noqa: E402
from auditflow_workflow import run_mvp_workflow  # noqa: E402
from create_fixture import create_fixture  # noqa: E402


FIXTURES = ROOT / "tools" / "enterprise-fixtures" / "fixtures"
OUT = ROOT / "tools" / "enterprise-fixtures" / "out"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    ensure_synthetic_fixture()
    results = [run_fixture(fixture_json) for fixture_json in sorted(FIXTURES.glob("*/fixture.json"))]
    suite = {
        "fixture_count": len(results),
        "passed": sum(1 for result in results if result["passed"]),
        "failed": sum(1 for result in results if not result["passed"]),
        "results": results,
    }
    (OUT / "enterprise-fixture-results.json").write_text(json.dumps(suite, indent=2), encoding="utf-8")
    (OUT / "enterprise-fixture-summary.md").write_text(render_markdown(suite), encoding="utf-8")
    print(json.dumps({
        "fixture_count": suite["fixture_count"],
        "passed": suite["passed"],
        "failed": suite["failed"],
        "results": str(OUT / "enterprise-fixture-results.json"),
        "summary": str(OUT / "enterprise-fixture-summary.md"),
    }, indent=2))


def run_fixture(fixture_json: Path) -> dict[str, Any]:
    fixture_dir = fixture_json.parent
    config = json.loads(fixture_json.read_text(encoding="utf-8"))
    prior = fixture_dir / config["prior_deck"]
    findings = fixture_dir / config["findings_workbook"]
    export = OUT / config["id"] / "export.pptx"
    report = OUT / config["id"] / "report.json"
    manifest = OUT / config["id"] / "manifest.json"
    export.parent.mkdir(parents=True, exist_ok=True)

    source_failures = [diagnostic.to_dict() for diagnostic in analyze_failure_modes(prior)]
    result = run_mvp_workflow(
        prior_deck=prior,
        findings_workbook=findings,
        output_deck=export,
        fiscal_year=int(config.get("fiscal_year", 2026)),
        report_path=report,
        manifest_path=manifest,
    )
    output_failures = [diagnostic.to_dict() for diagnostic in analyze_failure_modes(export)]
    passed = (
        result.preservation_score >= float(config.get("minimum_preservation_score", 1.0))
        and result.package_valid == bool(config.get("expected_package_valid", True))
        and not output_failures
    )
    return {
        "id": config["id"],
        "name": config["name"],
        "deck_type": config["deck_type"],
        "passed": passed,
        "export": str(export),
        "report": str(report),
        "manifest": str(manifest),
        "preservation_score": result.preservation_score,
        "package_valid": result.package_valid,
        "source_failures": source_failures,
        "output_failures": output_failures,
    }


def ensure_synthetic_fixture() -> None:
    fixture_dir = FIXTURES / "synthetic-audit-committee"
    prior = fixture_dir / "prior.pptx"
    findings = fixture_dir / "findings.xlsx"
    if not prior.exists():
        create_fixture(prior)
    if not findings.exists():
        wb = Workbook()
        ws = wb.active
        ws.title = "Findings"
        ws.append(["Finding Title", "Risk Rating", "Condition", "Recommendation", "Owner", "Due Date", "Status"])
        ws.append([
            "Privileged Access Review",
            "High",
            "Privileged access reviews lacked complete approval evidence.",
            "Require quarterly evidence capture and exception escalation.",
            "IT",
            "2026-09-30",
            "Open",
        ])
        ws.append([
            "Vendor Access Monitoring",
            "Medium",
            "Vendor access review evidence was inconsistently retained.",
            "Centralize vendor access review evidence and owner attestations.",
            "Procurement",
            "2026-10-31",
            "Open",
        ])
        wb.save(findings)


def render_markdown(suite: dict[str, Any]) -> str:
    rows = [
        f"| {item['id']} | {item['deck_type']} | {item['passed']} | {item['preservation_score']} | {item['package_valid']} | {len(item['output_failures'])} |"
        for item in suite["results"]
    ]
    return "\n".join([
        "# Enterprise Fixture Suite Summary",
        "",
        f"Fixtures: `{suite['fixture_count']}`",
        f"Passed: `{suite['passed']}`",
        f"Failed: `{suite['failed']}`",
        "",
        "| Fixture | Type | Passed | Preservation | Package Valid | Output Failures |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
        *rows,
        "",
    ])


if __name__ == "__main__":
    main()

