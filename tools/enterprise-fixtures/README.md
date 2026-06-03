# Enterprise Fixture Intake Framework

This framework validates real client-style recurring presentation decks against the AuditFlow AI preservation workflow.

Supported fixture types:

- Audit committee decks.
- Board decks.
- Consulting decks.
- Finance presentations.
- Recurring reporting decks.

## Fixture Intake Process

Every real-world fixture should be anonymized before it enters this repository. The fixture folder should contain only the prior recurring deck, the matching findings workbook, and optional notes needed to reproduce the workflow.

Intake checklist:

1. Remove customer names, people names, emails, account numbers, and confidential business data.
2. Preserve PowerPoint structure, masters, layouts, charts, tables, notes, placeholders, sectioning, and representative formatting.
3. Confirm the workbook keeps the same column semantics as the customer source workbook.
4. Add `fixture.json` metadata and success metrics.
5. Run the fixture suite.
6. Review `enterprise-fixture-summary.md`, `enterprise-fixture-results.json`, and `real-world-validation-report.json`.
7. Keep the fixture in regression only if it is safe to store and representative of a pilot workflow.

Supported fixture categories:

- `audit_committee`
- `board_deck`
- `consulting`
- `finance`
- `recurring_reporting`

## Adding A Fixture

Create a fixture folder under `tools/enterprise-fixtures/fixtures/{fixture-id}/`:

```text
fixture.json
prior.pptx
findings.xlsx
notes.txt       optional
```

`fixture.json`:

```json
{
  "id": "client-style-audit-deck",
  "name": "Client-style audit committee deck",
  "deck_type": "audit_committee",
  "fixture_profile": {
    "industry": "financial_services",
    "source": "anonymized_customer_style",
    "anonymized": true,
    "contains_customer_data": false,
    "deck_family": "quarterly_audit_committee"
  },
  "prior_deck": "prior.pptx",
  "findings_workbook": "findings.xlsx",
  "fiscal_year": 2026,
  "success_metrics": {
    "minimum_preservation_score": 0.98,
    "expected_package_valid": true,
    "max_blocking_output_failures": 0,
    "requires_manifest": true,
    "requires_editable_output": true
  }
}
```

Run:

```powershell
& "C:\Users\alexh\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" tools\enterprise-fixtures\run_fixture_suite.py
```

Outputs:

- `tools/enterprise-fixtures/out/enterprise-fixture-results.json`
- `tools/enterprise-fixtures/out/enterprise-fixture-summary.md`
- `tools/enterprise-fixtures/out/real-world-validation-report.json`

## Success Metrics

Default pilot metrics:

- Preservation score at or above `0.98`.
- Package validation passes.
- No critical or high-severity output failures.
- Editable text remains present.
- Operation manifest is generated.
- Table, chart, and slide duplication operations are explainable in the manifest.

## Failure Categories

The fixture suite classifies diagnostics into these categories:

- `malformed_template`
- `missing_asset`
- `broken_relationship`
- `unsupported_chart`
- `unsupported_smartart`
- `corrupted_embedded_workbook`
- `export_integrity`

Each diagnostic includes a severity, package part, message, and remediation action.
