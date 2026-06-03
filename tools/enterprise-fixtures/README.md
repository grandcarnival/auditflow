# Enterprise Fixture Intake Framework

This framework validates real client-style recurring presentation decks against the AuditFlow AI preservation workflow.

Supported fixture types:

- Audit committee decks.
- Board decks.
- Consulting decks.
- Finance presentations.
- Recurring reporting decks.

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
  "prior_deck": "prior.pptx",
  "findings_workbook": "findings.xlsx",
  "fiscal_year": 2026,
  "minimum_preservation_score": 1.0,
  "expected_package_valid": true
}
```

Run:

```powershell
& "C:\Users\alexh\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" tools\enterprise-fixtures\run_fixture_suite.py
```

Outputs:

- `tools/enterprise-fixtures/out/enterprise-fixture-results.json`
- `tools/enterprise-fixtures/out/enterprise-fixture-summary.md`

