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

from auditflow_pptx import analyze_failure_modes, collect_metrics, summarize_failure_diagnostics  # noqa: E402
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
        "pilot_ready": sum(1 for result in results if result["readiness"] == "pilot_ready"),
        "needs_review": sum(1 for result in results if result["readiness"] == "needs_review"),
        "blocked": sum(1 for result in results if result["readiness"] == "blocked"),
        "results": results,
    }
    (OUT / "enterprise-fixture-results.json").write_text(json.dumps(suite, indent=2), encoding="utf-8")
    (OUT / "enterprise-fixture-summary.md").write_text(render_markdown(suite), encoding="utf-8")
    (OUT / "real-world-validation-report.json").write_text(json.dumps(build_validation_report(suite), indent=2), encoding="utf-8")
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

    source_diagnostics = analyze_failure_modes(prior)
    source_failures = [diagnostic.to_dict() for diagnostic in source_diagnostics]
    source_failure_summary = summarize_failure_diagnostics(source_diagnostics)
    result = run_mvp_workflow(
        prior_deck=prior,
        findings_workbook=findings,
        output_deck=export,
        fiscal_year=int(config.get("fiscal_year", 2026)),
        report_path=report,
        manifest_path=manifest,
    )
    output_diagnostics = analyze_failure_modes(export)
    output_failures = [diagnostic.to_dict() for diagnostic in output_diagnostics]
    output_failure_summary = summarize_failure_diagnostics(output_diagnostics)
    success_metrics = _success_metrics(config)
    passed = (
        result.preservation_score >= success_metrics["minimum_preservation_score"]
        and result.package_valid == success_metrics["expected_package_valid"]
        and not output_failure_summary["blocking"]
        and output_failure_summary["by_severity"].get("critical", 0) + output_failure_summary["by_severity"].get("high", 0)
        <= success_metrics["max_blocking_output_failures"]
    )
    readiness = classify_readiness(passed, result.preservation_score, source_failure_summary, output_failure_summary)
    return {
        "id": config["id"],
        "name": config["name"],
        "deck_type": config["deck_type"],
        "fixture_profile": config.get("fixture_profile", {}),
        "passed": passed,
        "readiness": readiness,
        "export": str(export),
        "report": str(report),
        "manifest": str(manifest),
        "preservation_score": result.preservation_score,
        "package_valid": result.package_valid,
        "success_metrics": success_metrics,
        "source_metrics": collect_metrics(prior).to_dict(),
        "output_metrics": collect_metrics(export).to_dict(),
        "source_failures": source_failures,
        "output_failures": output_failures,
        "source_failure_summary": source_failure_summary,
        "output_failure_summary": output_failure_summary,
        "remediation_recommendations": _recommendations(source_failure_summary, output_failure_summary),
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
        f"| {item['id']} | {item['deck_type']} | {item['readiness']} | {item['passed']} | {item['preservation_score']} | {item['package_valid']} | {item['output_failure_summary']['total']} |"
        for item in suite["results"]
    ]
    return "\n".join([
        "# Enterprise Fixture Suite Summary",
        "",
        f"Fixtures: `{suite['fixture_count']}`",
        f"Passed: `{suite['passed']}`",
        f"Failed: `{suite['failed']}`",
        f"Pilot ready: `{suite['pilot_ready']}`",
        f"Needs review: `{suite['needs_review']}`",
        f"Blocked: `{suite['blocked']}`",
        "",
        "| Fixture | Type | Readiness | Passed | Preservation | Package Valid | Output Failures |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: |",
        *rows,
        "",
    ])


def classify_readiness(
    passed: bool,
    preservation_score: float,
    source_failures: dict[str, Any],
    output_failures: dict[str, Any],
) -> str:
    if output_failures["blocking"] or output_failures["by_severity"].get("critical", 0):
        return "blocked"
    if passed and preservation_score >= 0.98 and not source_failures["blocking"]:
        return "pilot_ready"
    return "needs_review"


def build_validation_report(suite: dict[str, Any]) -> dict[str, Any]:
    aggregate_failure_types: dict[str, int] = {}
    aggregate_recommendations: list[str] = []
    for result in suite["results"]:
        for failure_type, count in result["output_failure_summary"]["by_type"].items():
            aggregate_failure_types[failure_type] = aggregate_failure_types.get(failure_type, 0) + count
        for action in result["remediation_recommendations"]:
            if action not in aggregate_recommendations:
                aggregate_recommendations.append(action)
    return {
        "summary": {
            "fixture_count": suite["fixture_count"],
            "passed": suite["passed"],
            "failed": suite["failed"],
            "pilot_ready": suite["pilot_ready"],
            "needs_review": suite["needs_review"],
            "blocked": suite["blocked"],
        },
        "success_metrics": {
            "minimum_preservation_score": 0.98,
            "package_valid": True,
            "max_blocking_output_failures": 0,
            "manifest_required": True,
            "editable_output_required": True,
        },
        "aggregate_output_failure_types": aggregate_failure_types,
        "aggregate_recommendations": aggregate_recommendations,
        "results": suite["results"],
    }


def _success_metrics(config: dict[str, Any]) -> dict[str, Any]:
    metrics = config.get("success_metrics", {})
    return {
        "minimum_preservation_score": float(metrics.get("minimum_preservation_score", config.get("minimum_preservation_score", 0.98))),
        "expected_package_valid": bool(metrics.get("expected_package_valid", config.get("expected_package_valid", True))),
        "max_blocking_output_failures": int(metrics.get("max_blocking_output_failures", 0)),
        "requires_manifest": bool(metrics.get("requires_manifest", True)),
        "requires_editable_output": bool(metrics.get("requires_editable_output", True)),
    }


def _recommendations(source_summary: dict[str, Any], output_summary: dict[str, Any]) -> list[str]:
    recommendations: list[str] = []
    for action in source_summary["recommended_actions"] + output_summary["recommended_actions"]:
        if action not in recommendations:
            recommendations.append(action)
    if output_summary["blocking"]:
        recommendations.append("Do not pilot this fixture until blocking output diagnostics are resolved.")
    if not recommendations:
        recommendations.append("No remediation required for this fixture under current MVP checks.")
    return recommendations


if __name__ == "__main__":
    main()
