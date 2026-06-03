from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "tools" / "regression" / "out"
PYTHON = Path(sys.executable)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    steps = [
        run_step("unit_tests", [str(PYTHON), "-m", "pytest", "packages/pptx/tests", "packages/documents/tests", "packages/ai/tests", "packages/workflow/tests"]),
        run_step("preservation_benchmark", [str(PYTHON), "tools/preservation-benchmark/run_benchmark_suite.py"]),
        run_step("enterprise_fixtures", [str(PYTHON), "tools/enterprise-fixtures/run_fixture_suite.py"]),
    ]
    passed = all(step["returncode"] == 0 for step in steps)
    result = {"passed": passed, "steps": steps}
    (OUT / "regression-results.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    (OUT / "regression-summary.md").write_text(render_markdown(result), encoding="utf-8")
    print(json.dumps({
        "passed": passed,
        "results": str(OUT / "regression-results.json"),
        "summary": str(OUT / "regression-summary.md"),
    }, indent=2))
    if not passed:
        raise SystemExit(1)


def run_step(name: str, command: list[str]) -> dict[str, Any]:
    completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    return {
        "name": name,
        "command": command,
        "returncode": completed.returncode,
        "stdout_tail": completed.stdout[-4000:],
        "stderr_tail": completed.stderr[-4000:],
    }


def render_markdown(result: dict[str, Any]) -> str:
    rows = [
        f"| {step['name']} | {step['returncode'] == 0} | `{step['returncode']}` |"
        for step in result["steps"]
    ]
    return "\n".join([
        "# Regression Suite Summary",
        "",
        f"Passed: `{result['passed']}`",
        "",
        "| Step | Passed | Return Code |",
        "| --- | ---: | ---: |",
        *rows,
        "",
    ])


if __name__ == "__main__":
    main()

