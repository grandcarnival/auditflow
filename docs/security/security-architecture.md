# Security Architecture

## Security Goals

- Strong tenant isolation.
- Least-privilege data access.
- Auditable AI and document processing.
- No public exposure of service keys or secrets.
- Enterprise-ready controls for confidential audit materials.

## Authentication

- Supabase Auth.
- Cookie-backed SSR auth in Next.js.
- Server-side user revalidation via `getUser()` for protected operations.
- SSO-ready user model.

## Authorization And RBAC

Roles:

- Owner: billing, members, settings, all projects, deletion.
- Admin: members, projects, exports, settings except billing ownership transfer.
- Member: create and edit projects, upload files, run generation, review artifacts.
- Viewer: read-only access to projects and exports.

RBAC must be enforced in:

- Postgres RLS policies.
- Server-side service functions.
- UI affordances.

The UI is never the source of authorization truth.

## Data Isolation

- Every tenant row carries `organization_id`.
- Storage paths include organization and project ids.
- Retrieval metadata includes organization and project ids.
- AI workflows receive only scoped content for the active project.
- Background jobs validate tenant context before reading or writing.

## Secrets

- No service role key in browser code.
- Vercel environment variables scoped by environment.
- Stripe webhook secret required for webhook processing.
- OpenAI API keys server-only.
- Supabase publishable key can be exposed only as intended client key.

## File Security

- Validate MIME type and extension.
- Enforce file size limits by plan.
- Compute SHA-256 fingerprints.
- Scan files before processing when an AV service is selected.
- Store originals separately from derived artifacts.
- Signed URLs expire quickly.

## Audit Logging

Audit events should capture:

- Sign-in-sensitive account actions.
- Organization membership changes.
- Uploads and deletes.
- Processing starts and failures.
- AI generation events.
- Review approvals.
- Exports.
- Billing changes.

## Compliance Direction

MVP should be designed toward SOC 2 readiness:

- Access controls.
- Audit trails.
- Data retention.
- Vendor inventory.
- Incident response runbooks.
- Backup and restore procedures.

