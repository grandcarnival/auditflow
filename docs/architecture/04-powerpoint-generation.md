# PowerPoint Generation Architecture

## Goal

The platform must preserve and intelligently reuse existing PowerPoint formatting and layouts. This means the prior-year deck is treated as a design system and data source, not just a file to copy.

## Components

### Template Analyzer

Responsibilities:

- Parse PPTX package structure.
- Extract slide masters, layouts, themes, fonts, colors, placeholders, chart definitions, table styles, images, and relationships.
- Build slide fingerprints based on layout geometry and semantic role.
- Identify reusable repeated components such as headers, footers, labels, section dividers, status badges, legends, and chart frames.

### Slide Classifier

Responsibilities:

- Classify slides by role.
- Match requested output sections to prior-year slide patterns.
- Score confidence for each layout match.
- Flag ambiguous patterns for review.

### Content Binder

Responsibilities:

- Bind generated text, findings, tables, and charts into template placeholders.
- Maintain text styles, bullet levels, spacing, and theme colors.
- Detect overflow before export.
- Prefer editable PowerPoint text, tables, and charts over images.

### Renderer

Responsibilities:

- Generate editable PPTX output.
- Preserve masters and theme assets where feasible.
- Write generated artifacts to storage.
- Produce preview images for review.

### Validator

Responsibilities:

- Compare output deck against template constraints.
- Detect missing slides, broken relationships, clipped text, missing fonts, image-only fallbacks, and chart data inconsistencies.
- Emit review warnings and blockers.

## Preservation Techniques

- Use source deck as template seed.
- Copy master/theme assets forward.
- Maintain original slide dimensions.
- Preserve theme colors and font declarations.
- Use placeholder geometry from matched prior-year slides.
- Generate new slides by cloning slide patterns and rebinding content.
- Keep a layout-pattern library per project and optionally promote high-quality templates to organization-level reusable templates.

## Implementation Spike Required

The highest-risk engineering question is whether the selected Node PPTX stack can preserve enough source Open XML fidelity. The first technical spike must compare:

1. High-level generation with `pptxgenjs`.
2. Template cloning with Open XML package manipulation using `JSZip`.
3. A hybrid strategy: clone selected XML parts, then bind editable content.

Success criteria:

- Masters/themes preserved.
- Text remains editable.
- Charts remain editable where possible.
- Source branding survives round trip.
- Generated deck opens cleanly in PowerPoint, Keynote, and Google Slides where feasible.

