# Preview Deployment Guide

## Architecture Review

Current preview architecture:

- `apps/web` is the deployable Next.js 15 app.
- Vercel should build and host the public preview.
- `/` serves the upload/status/download UI.
- `/api/process` uploads files and queues jobs when `AUDITFLOW_PROCESSOR_MODE=supabase`.
- `/api/jobs/[id]` returns queued, processing, completed, or failed job state.
- `/api/exports/[id]` streams completed artifacts from Supabase Storage.

Current local architecture:

- The local app can run the Python preservation workflow through `tools/workflow/run_mvp_workflow.py`.
- Local processing writes files to `.runtime/jobs/{jobId}`.
- Local workflow depends on Python packages from `requirements.txt`.

Important deployment decision:

- Public preview now requires Supabase Storage/Postgres plus a Python worker for real processing.

## Required Environment Variables

Required for public preview:

- `NEXT_PUBLIC_APP_ENV=preview`
- `AUDITFLOW_PROCESSOR_MODE=supabase`
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `AUDITFLOW_STORAGE_BUCKET=auditflow-artifacts`

Optional for local development:

- `AUDITFLOW_PROCESSOR_MODE=local`
- `AUDITFLOW_REPO_ROOT=<absolute path to repository root>`
- `AUDITFLOW_PYTHON=<python executable>`

Future server-side integrations:

- `OPENAI_API_KEY`: required only when AI-assisted mapping is enabled.
- `SENTRY_DSN`: recommended before external pilot users.
- Storage variables are not required for the UI-only preview, but will be required before processing real decks.

Do not expose secrets through `NEXT_PUBLIC_*` variables.

## Required External Services

Required now:

- GitHub repository connected to Vercel.
- Vercel project configured with root directory `apps/web`.

Not required for first processing preview:

- Supabase.
- Stripe.
- Mixpanel.
- OpenAI.
- Sentry.

Required before broader real deck pilot:

- Sentry or equivalent error monitoring.
- Auth or preview access controls.

## Vercel Project Configuration

Use these Vercel settings:

- Framework preset: `Next.js`
- Root Directory: `apps/web`
- Install Command: `npm install`
- Build Command: `npm run build`
- Output Directory: leave default
- Development Command: `npm run dev`

The app includes `apps/web/vercel.json` with matching commands.

## Deployment Checklist

Before linking:

- GitHub repo is pushed.
- `apps/web/package.json` and `apps/web/package-lock.json` are committed.
- `apps/web/vercel.json` is committed.
- Build passes locally from `apps/web`.
- `AUDITFLOW_PROCESSOR_MODE=supabase` is set for Vercel preview.
- Supabase migration has been applied.
- Worker service is running.

After preview deploy:

- Open the Vercel preview URL.
- Confirm the AuditFlow AI page loads.
- Confirm uploading files creates a queued job.
- Confirm worker completes the job.
- Confirm PPTX download works.
- Confirm no server errors appear in Vercel logs.
- Confirm `/api/jobs/:id` reaches `completed`.

## Deployment Instructions

### Option A: Vercel Dashboard

1. Go to Vercel.
2. Import `grandcarnival/auditflow`.
3. Set Root Directory to `apps/web`.
4. Confirm Framework Preset is `Next.js`.
5. Add environment variables:
   - `NEXT_PUBLIC_APP_ENV=preview`
   - `AUDITFLOW_PROCESSOR_MODE=supabase`
   - `SUPABASE_URL`
   - `SUPABASE_SERVICE_ROLE_KEY`
   - `AUDITFLOW_STORAGE_BUCKET=auditflow-artifacts`
6. Deploy.
7. Open the preview URL.

### Option B: Vercel CLI

From the app directory:

```powershell
cd "C:\Users\alexh\Documents\Codex\2026-05-28\you-are-my-autonomous-cto-and\apps\web"
npm.cmd install
npm.cmd run build
npm.cmd install -g vercel
vercel login
vercel link
vercel env add NEXT_PUBLIC_APP_ENV preview
vercel env add AUDITFLOW_PROCESSOR_MODE preview
vercel env add SUPABASE_URL preview
vercel env add SUPABASE_SERVICE_ROLE_KEY preview
vercel env add AUDITFLOW_STORAGE_BUCKET preview
vercel deploy
```

When prompted for the env var values:

- `NEXT_PUBLIC_APP_ENV`: `preview`
- `AUDITFLOW_PROCESSOR_MODE`: `supabase`
- `AUDITFLOW_STORAGE_BUCKET`: `auditflow-artifacts`

## Current Deployment Blockers

Blocking real deck processing:

- Supabase project must be created and migrated.
- Worker service must be deployed and running.
- Preview currently has no auth, so it should be shared only with trusted users.

Not blocking public UI preview:

- Supabase is not configured.
- Stripe is not configured.
- OpenAI is not configured.
- Sentry is not configured.

## Next Deployment Step

Deploy Vercel + Supabase + one Python worker, then run one fixture upload end to end.
