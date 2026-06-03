# Testing Strategy

## Test Pyramid

### Unit Tests

- RBAC helper functions.
- Schema validators.
- Excel parser.
- PDF parser wrappers.
- PPTX layout classifier.
- Prompt output validators.
- Billing entitlement logic.

### Integration Tests

- Supabase RLS policies.
- Storage upload and access rules.
- Stripe webhook processing.
- AI workflow persistence.
- Processing job state transitions.
- Export artifact creation.

### End-To-End Tests

- Sign up, create organization, create project.
- Upload prior-year deck and findings workbook.
- Run processing.
- Review generated deck plan.
- Export PPTX.
- Billing checkout and portal flows in test mode.

### Regression Fixtures

Maintain a private fixture set:

- Simple prior-year deck.
- Branded enterprise deck.
- Findings-heavy workbook.
- PDF with tables.
- Notes-only case.
- Large deck.
- Edge cases with unusual fonts, charts, and nested shapes.

## AI Evaluation

AI outputs need deterministic validation plus qualitative evals:

- JSON schema validity.
- Citation coverage.
- Finding completeness.
- No unsupported claims.
- Prior-year delta accuracy.
- Executive summary tone.
- Layout selection accuracy.

## PowerPoint Validation

Automated checks:

- PPTX opens without repair.
- Expected slide count.
- Expected editable text objects.
- Expected charts/tables where possible.
- No known text overflow.
- Theme and slide dimensions preserved.
- Preview images generated.

Manual launch-readiness checks:

- Open in Microsoft PowerPoint.
- Open in Google Slides.
- Spot-check formatting fidelity against source deck.

