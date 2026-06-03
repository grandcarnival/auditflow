# Pilot Readiness Report

Date: 2026-06-03

## Current MVP Maturity

AuditFlow AI is ready for controlled internal and friendly-pilot validation against anonymized enterprise-style decks.

Current maturity estimate: `82%` for preservation-focused MVP validation.

Strengths:

- Editable PPTX export is working.
- PowerPoint Open XML preservation architecture is validated.
- Table updates, chart updates, slide duplication, notes preservation, and manifest generation are covered by tests and fixtures.
- Regression output shows 23 unit tests passing, preservation benchmark score `1.0`, and enterprise fixture suite passing.
- The web app builds successfully and exposes upload/process/download routes.
- Operation manifests make output mutations auditable.

## Known Limitations

- Current enterprise fixture coverage is still synthetic.
- Optional notes/context is collected by the UI but not yet mapped into generation logic.
- Linting is not configured.
- The web app's local processing path shells out to Python; deployed processing needs a dedicated production path.
- No durable production file storage is wired yet.
- No auth, RBAC, billing, or analytics should be considered pilot-ready.
- Human visual QA is still required for each real deck.

## Unsupported Or Review-Required PowerPoint Features

Unsupported or not yet safe for mutation:

- SmartArt content mutation.
- Unsupported chart families beyond current bar, line, and pie support.
- Complex embedded OLE objects.
- Corrupted embedded workbooks.
- Broken or missing relationships.
- Malformed PPTX package parts.
- Advanced animations and transitions.
- Heavily customized macros or VBA-enabled workflows.
- External linked assets.

The current posture should be preserve-as-is or block with diagnostics, not attempt unsafe mutation.

## Recommended Pilot Customer Profile

Best first pilot:

- A team with a recurring audit committee, finance, board, or consulting deck.
- Quarterly or annual refresh workflow.
- Decks between roughly 10 and 60 slides.
- Mostly standard PowerPoint layouts, text boxes, tables, and standard charts.
- Findings or metrics available in Excel.
- Willing to provide anonymized prior-year decks for benchmark fixtures.
- Values editable outputs and formatting preservation over generative creativity.

Avoid initial pilots with:

- Highly animated decks.
- Heavy SmartArt dependency.
- Macro-enabled or externally linked presentations.
- Very large media-heavy decks.
- Workflows requiring strict production auth, billing, or enterprise admin controls on day one.

## Top Technical Risks

1. Real deck variability.
   - Risk: customer decks may contain unsupported chart, SmartArt, embedded, or relationship patterns.
   - Mitigation: add every anonymized real deck as a fixture and fail regression on fidelity loss.

2. Production processing architecture.
   - Risk: local Python shell-out is not a clean Vercel production model.
   - Mitigation: spike Python Function or external worker with durable storage before external pilot.

3. Visual fidelity beyond structural validation.
   - Risk: Open XML validation can pass while a slide is visually off.
   - Mitigation: add human visual QA first, then screenshot/pixel comparison later.

4. Data sensitivity.
   - Risk: audit decks may contain confidential findings and management commentary.
   - Mitigation: anonymize fixtures, minimize logs, use private storage, and avoid client-side AI calls.

5. AI mapping hallucination.
   - Risk: AI-assisted mapping could invent unsupported content.
   - Mitigation: deterministic mapping first, structured outputs, confidence thresholds, and fallback rules.

## Deployment Checklist

Before a pilot user uploads a real deck:

- Build passes from `apps/web`.
- Regression suite passes.
- Enterprise fixture suite passes with at least one anonymized real deck.
- Vercel project root is configured as `apps/web`.
- Production processing path is selected.
- Durable private storage is configured.
- `OPENAI_API_KEY` is configured server-side only if AI mapping is enabled.
- Upload size limits and file validation are enforced.
- Sentry is configured for server/API errors.
- Generated PPTX, report, and manifest are downloadable.
- Retention/deletion policy is documented.
- Human review checklist is ready.

## Pilot Gate

Proceed to pilot when at least three anonymized enterprise-style fixtures pass:

- One audit committee or board deck.
- One finance or recurring reporting deck.
- One consulting-style deck.

Each fixture must produce:

- Editable PPTX.
- Preservation report.
- Operation manifest.
- No blocking output diagnostics.
- Preservation score at or above `0.98`.
