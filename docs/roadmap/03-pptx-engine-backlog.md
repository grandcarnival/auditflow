# PPTX Engine Backlog

## Milestone 1: Preservation Core

- Create `packages/pptx` TypeScript package.
- Implement PPTX ZIP reader.
- Implement package metrics collector.
- Implement slide text extraction.
- Implement safe text replacement preserving all unrelated package parts.
- Add fixture-based tests.

Acceptance criteria:

- Source masters, layouts, themes, notes, tables, charts, and placeholders remain present after text replacement.
- Output opens as a valid ZIP/PPTX package.
- Editable text remains editable.

## Milestone 2: Template Analysis

- Extract slide dimensions.
- Extract slide masters and layouts.
- Extract theme colors and font metadata.
- Extract placeholder geometry.
- Extract table and chart presence.
- Extract speaker note text.
- Classify basic slide roles.

Acceptance criteria:

- Prior-year deck produces a reusable template model.
- Each slide has a layout fingerprint and semantic role candidate.

## Milestone 3: Content Mapping

- Define JSON schema for deck content map.
- Map findings data to candidate slide patterns.
- Generate replacement operations for title, summary, and finding detail slides.

Acceptance criteria:

- A deterministic content map can regenerate a current-year deck from a prior-year fixture.

## Milestone 4: Tables And Charts

- Replace table cell values while preserving table styles.
- Replace chart embedded workbook values.
- Validate chart XML consistency.

Acceptance criteria:

- Findings summary table and chart update from Excel-derived data while remaining editable.

## Milestone 5: Slide Duplication

- Duplicate selected slide patterns.
- Remap slide ids and relationships.
- Preserve notes, charts, media, and layout references.

Acceptance criteria:

- Multiple findings pages can be generated from one prior-year finding slide pattern.

