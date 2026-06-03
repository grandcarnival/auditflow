# Backend Services

## Service Boundary Overview

AuditFlow AI should use modular backend services even if the initial implementation lives in a monorepo. Each service owns a clear domain and can later move to dedicated workers if runtime needs grow.

## Auth And Identity Service

Responsibilities:

- Supabase Auth integration.
- Session validation.
- User profile bootstrap.
- Invitation acceptance.
- SSO-ready identity mapping.

Primary tables:

- `organization_memberships`
- `audit_events`

## Organization Service

Responsibilities:

- Organization creation.
- Member management.
- Role updates.
- Workspace settings.
- Tenant context resolution.

Primary tables:

- `organizations`
- `organization_memberships`

## Project Service

Responsibilities:

- Audit project lifecycle.
- Project status.
- Artifact version visibility.
- Review state transitions.

Primary tables:

- `projects`
- `generated_artifacts`
- `review_comments`

## Upload Service

Responsibilities:

- Signed uploads.
- Storage path generation.
- File validation.
- File fingerprinting.
- Source file records.

Primary tables:

- `source_files`

Storage paths:

- `org/{organization_id}/project/{project_id}/source/{source_file_id}/{filename}`
- `org/{organization_id}/project/{project_id}/artifacts/{artifact_id}/{filename}`

## Processing Service

Responsibilities:

- Job creation.
- Job locking.
- State transitions.
- Retry policy.
- Failure persistence.
- Progress events.

Primary tables:

- `processing_jobs`

## Extraction Service

Responsibilities:

- PPTX template extraction.
- XLSX findings extraction.
- PDF text and table extraction.
- Notes normalization.
- Citation mapping.

Primary tables:

- `extracted_documents`
- `deck_templates`

## AI Workflow Service

Responsibilities:

- Prompt registry.
- Structured output generation.
- Retrieval orchestration.
- AI run metadata.
- Validation calls.

Primary tables:

- `ai_runs`
- `generated_artifacts`

## PowerPoint Service

Responsibilities:

- Slide pattern matching.
- Content binding.
- Chart/table creation.
- PPTX rendering.
- Preview generation.
- Export validation.

Primary tables:

- `deck_templates`
- `generated_artifacts`

## Billing Service

Responsibilities:

- Checkout.
- Customer portal.
- Webhooks.
- Entitlements.
- Usage metering.

Primary tables:

- `billing_customers`
- `subscriptions`
- `usage_events`

## Observability Service

Responsibilities:

- Sentry error capture.
- Mixpanel event capture.
- Audit log writes.
- Job event logs.
- Operational diagnostics.

