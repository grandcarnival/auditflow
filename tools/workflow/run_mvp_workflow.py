from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "packages" / "ai"))
sys.path.insert(0, str(ROOT / "packages" / "documents"))
sys.path.insert(0, str(ROOT / "packages" / "pptx"))
sys.path.insert(0, str(ROOT / "packages" / "workflow"))

from auditflow_workflow import run_mvp_workflow  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the AuditFlow AI MVP workflow.")
    parser.add_argument("--prior-deck", required=True)
    parser.add_argument("--findings-workbook", required=True)
    parser.add_argument("--output-deck", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--manifest")
    parser.add_argument("--fiscal-year", type=int, default=2026)
    args = parser.parse_args()

    result = run_mvp_workflow(
        prior_deck=args.prior_deck,
        findings_workbook=args.findings_workbook,
        output_deck=args.output_deck,
        fiscal_year=args.fiscal_year,
        report_path=args.report,
        manifest_path=args.manifest,
    )
    print(json.dumps(result.to_dict()))


if __name__ == "__main__":
    main()
