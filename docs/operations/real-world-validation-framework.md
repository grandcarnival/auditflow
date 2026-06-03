# Real-World Validation Framework

## Objective

AuditFlow AI should prove preservation fidelity against customer-style recurring decks before broad MVP rollout. The validation framework is designed to make each pilot run explainable, repeatable, and regression-safe.

## Intake Workflow

1. Receive a recurring deck and matching workbook from a pilot-style workflow.
2. Anonymize all sensitive data while preserving the original PowerPoint structure.
3. Add the deck as a fixture under `tools/enterprise-fixtures/fixtures/{fixture-id}`.
4. Define `fixture.json` metadata and success metrics.
5. Run `tools/enterprise-fixtures/run_fixture_suite.py`.
6. Review the generated export, preservation report, operation manifest, and validation report.
7. Keep accepted fixtures in regression so future changes cannot silently reduce fidelity.

## Success Metrics

Pilot-ready fixture targets:

- Preservation score: `>= 0.98`.
- Package validation: valid.
- Blocking output failures: `0`.
- Notes preservation: true when source notes exist.
- Theme/layout/master preservation: true.
- Chart/table preservation: true for supported chart/table types.
- Editable output: editable text present and PPTX package intact.
- Manifest completeness: source metadata, workbook metadata, modified slides, duplicated slides, tables, charts, mappings, validation, warnings, and fallback behavior recorded.

## Failure Categories

Critical or high-severity failures block pilot use:

- Malformed template.
- Missing assets.
- Broken relationships.
- Corrupted embedded workbooks.
- Export integrity failures.

Medium-severity failures require review:

- Unsupported chart types.
- Unsupported SmartArt.
- Unsupported embedded object mutations.

Low-severity failures should be logged but may not block a pilot:

- Non-mutated decorative objects.
- Minor unsupported metadata.
- Non-critical warnings with preserved output.

## Benchmark Reporting

Every run should produce:

- `enterprise-fixture-results.json`: machine-readable fixture outcomes.
- `enterprise-fixture-summary.md`: human-readable summary.
- `real-world-validation-report.json`: pilot readiness rollup with aggregate failures and remediation recommendations.
- Per-fixture `report.json`: preservation and content update details.
- Per-fixture `manifest.json`: auditable operation manifest.
- Per-fixture `export.pptx`: generated editable output.

## Pilot Acceptance Gate

A fixture is pilot-ready only when:

- The generated deck opens in PowerPoint.
- The generated deck remains editable.
- Validation reports no blocking output failures.
- The preservation score meets the configured threshold.
- The operation manifest explains every mutation.
- A human reviewer confirms the regenerated deck is visually acceptable.

## Regression Rule

Every accepted enterprise-style fixture becomes part of the regression suite. A future change that reduces preservation fidelity, corrupts output, removes manifest coverage, or introduces blocking diagnostics should fail regression.
