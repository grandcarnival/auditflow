# AuditFlow AI Web App

This directory contains the first lightweight Next.js MVP scaffold.

Implemented:

- Next.js 15
- TypeScript
- Minimal upload UI
- Processing status
- Preservation report display
- Editable PPTX download route

Local processing calls `tools/workflow/run_mvp_workflow.py`, which runs the current Python preservation workflow.

## Local Development

```powershell
npm.cmd install
npm.cmd run dev
```

For local processing, set:

```powershell
$env:AUDITFLOW_PROCESSOR_MODE="local"
$env:AUDITFLOW_REPO_ROOT="C:\Users\alexh\Documents\Codex\2026-05-28\you-are-my-autonomous-cto-and"
```

## Vercel Preview

Deploy this directory as the Vercel project root:

```text
apps/web
```

Set preview environment variables:

```text
NEXT_PUBLIC_APP_ENV=preview
AUDITFLOW_PROCESSOR_MODE=supabase
SUPABASE_URL=<your Supabase project URL>
SUPABASE_SERVICE_ROLE_KEY=<server-side service role key>
AUDITFLOW_STORAGE_BUCKET=auditflow-artifacts
```

The public preview uses Supabase for durable job state and artifact storage. A Python worker must also be running for jobs to move from `queued` to `completed`.

Planned next:

- Add Tailwind and shadcn/ui once package manager access is available.
- Add authentication before sharing with broader pilot users.
