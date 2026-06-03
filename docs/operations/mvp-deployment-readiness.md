# MVP Deployment Readiness

## Current Readiness

The Next.js app builds locally, but the processing architecture is not yet ready for a simple Vercel production deployment. The current API route shells out to Python to run the PPTX workflow. That is acceptable for local MVP validation, but production needs a deliberate processing path.

## Deployment Decision

Recommended pilot deployment path:

1. Keep the Next.js app on Vercel.
2. Move PPTX processing into a dedicated Python worker or Vercel Python Function spike.
3. Store uploaded and generated files in durable object storage.
4. Return job status and download URLs from the web app.

Reasoning:

- Vercel supports Python Functions, but the runtime is still marked Beta in the official docs.
- Vercel Functions have package size and execution limits that may become tight for large PowerPoint files.
- The current local workflow writes to `.runtime`, which is not durable production storage.

Reference points:

- Vercel Python runtime: https://vercel.com/docs/functions/runtimes/python
- Vercel environment variables: https://vercel.com/docs/environment-variables
- Vercel function limits: https://vercel.com/docs/functions/limitations
- OpenAI authentication: https://platform.openai.com/docs/api-reference
- OpenAI structured outputs: https://platform.openai.com/docs/guides/structured-outputs

## Environment Variables

Required for a pilot deployment:

- `OPENAI_API_KEY`: server-side only.
- `AUDITFLOW_PYTHON`: optional local override for the Python executable.
- `AUDITFLOW_STORAGE_BUCKET`: required once object storage is wired.
- `AUDITFLOW_STORAGE_ACCESS_KEY`: required once object storage is wired.
- `AUDITFLOW_STORAGE_SECRET_KEY`: required once object storage is wired.
- `SENTRY_DSN`: optional for pilot, recommended before external testing.
- `NEXT_PUBLIC_APP_ENV`: optional environment label.

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
- Add environment variables for preview and production.
- Confirm whether processing will run as a Python Function, external worker, or separate service.
- Replace `.runtime` file persistence for deployed processing.
- Add upload size limits and file-type validation before external users.
- Add Sentry before pilot users process real decks.
- Run a full upload/download smoke test against a preview deployment.

## Current Blockers

- Production processing path is not finalized.
- Durable storage is not wired.
- ESLint is not configured.
- `npm audit` still needs a clean local or CI run.
- Real customer-style fixtures have not yet been added.
