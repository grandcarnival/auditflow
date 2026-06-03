# MVP Deployment Readiness

## Current Readiness

The Next.js app builds locally and can be deployed as a public Vercel preview. The preview can now support pilot processing when connected to Supabase Storage/Postgres and a running Python worker.

## Deployment Decision

Recommended pilot deployment path:

1. Keep the Next.js app on Vercel.
2. Use Supabase Postgres for job state.
3. Use Supabase Storage for uploaded files and generated artifacts.
4. Run the Python preservation engine in a small background worker.
5. Return job status and download URLs from the web app.

Reasoning:

- Vercel supports Python Functions and currently lists Python 3.12, 3.13, and 3.14, but PPTX processing is better handled by an always-on worker during pilot.
- Supabase Storage provides private file buckets and access controls.
- Supabase Postgres gives a simple durable job lifecycle without adding a separate queue service.

Reference points:

- Vercel Python runtime: https://vercel.com/docs/functions/runtimes/python
- Vercel environment variables: https://vercel.com/docs/environment-variables
- Vercel function limits: https://vercel.com/docs/functions/limitations
- OpenAI authentication: https://platform.openai.com/docs/api-reference
- OpenAI structured outputs: https://platform.openai.com/docs/guides/structured-outputs

## Environment Variables

Required for a pilot deployment:

- `NEXT_PUBLIC_APP_ENV`: set to `preview` for public preview.
- `AUDITFLOW_PROCESSOR_MODE`: set to `supabase` for pilot preview; set to `local` only for local development.
- `SUPABASE_URL`: Supabase project URL.
- `SUPABASE_SERVICE_ROLE_KEY`: server-side only service role key.
- `AUDITFLOW_STORAGE_BUCKET`: defaults to `auditflow-artifacts`.
- `OPENAI_API_KEY`: server-side only.
- `AUDITFLOW_PYTHON`: optional local override for the Python executable.
- `AUDITFLOW_REPO_ROOT`: optional local override for the repository root.
- `SENTRY_DSN`: optional for pilot, recommended before external testing.

Vercel environment variables are scoped by environment and apply only to new deployments after changes. Secrets must not be exposed to client-side code.

## Storage Requirements

Pilot storage must support:

- Prior deck upload.
- Findings workbook upload.
- Generated PPTX download.
- Preservation report.
- Operation manifest.
- Short retention windows and manual deletion.

Storage should be private by default. Download links should be short-lived once auth is introduced.

## OpenAI Integration Requirements

The current MVP workflow is deterministic and does not require OpenAI to generate an export. When AI-assisted mapping is enabled, it should use:

- Server-side API key loading from environment variables.
- Structured outputs with JSON schema validation.
- Confidence scoring and deterministic fallback logic.
- No direct client-side calls to OpenAI.
- Logging that records model ID, prompt version, schema version, and confidence without storing sensitive deck text unnecessarily.

## Vercel Checklist

- Configure Vercel project root as `apps/web`.
- Keep `npm run build` passing from `apps/web`.
- Add `NEXT_PUBLIC_APP_ENV=preview`.
- Add `AUDITFLOW_PROCESSOR_MODE=supabase`.
- Add `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, and `AUDITFLOW_STORAGE_BUCKET`.
- Apply the Supabase processing migration.
- Deploy and run the Python worker.
- Add upload size limits and file-type validation before external users.
- Add Sentry before pilot users process real decks.
- Run a full upload/download smoke test against a preview deployment.

## Current Blockers

- Supabase project must be created and migrated.
- Python worker must be deployed.
- ESLint is not configured.
- `npm audit` still needs a clean local or CI run.
- Real customer-style fixtures have not yet been added.
