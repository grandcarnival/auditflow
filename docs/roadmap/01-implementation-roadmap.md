# Implementation Roadmap

## Phase 0: Approval And Technical Spikes

Goals:

- Approve architecture and repo structure.
- Validate PowerPoint preservation feasibility.
- Validate PDF and Excel extraction stack.
- Confirm hosted OpenAI retrieval versus self-managed retrieval.
- Confirm Supabase project, Vercel project, Stripe mode, Sentry, and Mixpanel access.

Exit criteria:

- Round-trip PPTX spike completed.
- Extraction spike completed.
- Architecture approved.
- Implementation backlog created.

## Phase 1: Platform Foundation

Deliverables:

- Next.js 15 app scaffold with TypeScript, Tailwind, shadcn/ui.
- Supabase local/config baseline.
- Auth flow.
- Organization and membership model.
- RBAC checks.
- Project dashboard shell.
- Storage buckets and signed upload flow.
- Sentry and Mixpanel initialization.
- GitHub Actions for lint, typecheck, unit tests, and build.
- Vercel staging deployment.

## Phase 2: Upload And Extraction MVP

Deliverables:

- Project creation.
- Multi-file upload for PPTX, XLSX, PDF, and notes.
- File validation and metadata capture.
- Excel findings parser.
- PDF text extraction.
- PPTX template analyzer v1.
- Extraction artifacts persisted.
- Processing job state machine.

## Phase 3: AI Structured Workflows

Deliverables:

- Prompt registry.
- Structured finding extraction.
- Executive summary generation.
- Deck plan generation.
- Retrieval indexing and metadata filters.
- AI run logging and replay metadata.
- Review warnings.

## Phase 4: PowerPoint Export MVP

Deliverables:

- Layout pattern matching.
- Editable slide generation.
- Findings pages.
- Executive summary slides.
- Chart generation.
- PPTX export.
- Preview images.
- Validation report.

## Phase 5: Review Workflow And Enterprise Controls

Deliverables:

- In-app review of generated deck plan.
- Commenting and approval.
- Version history.
- Audit logs.
- Team invitations.
- Data retention controls.
- Export history.

## Phase 6: Billing And Entitlements

Deliverables:

- Stripe Checkout or customer portal.
- Webhook ingestion.
- Subscription state sync.
- Seat limits.
- Usage limits.
- Plan-based entitlements.

## Phase 7: Hardening And Launch Readiness

Deliverables:

- Security review.
- RLS advisor pass.
- Load and file-size testing.
- AI eval set.
- Regression fixture decks.
- Runbooks.
- Backup and restore drills.
- Production deployment checklist.

