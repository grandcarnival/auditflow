# AuditFlow AI Processing Worker

This worker processes queued pilot jobs from Supabase.

It is intentionally small:

- Polls `auditflow_jobs` for `queued` jobs.
- Marks a job `processing`.
- Downloads prior PPTX and findings workbook from Supabase Storage.
- Runs the Python preservation workflow.
- Uploads generated PPTX, report, and manifest.
- Marks the job `completed` or `failed`.

## Required Environment Variables

```text
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
AUDITFLOW_STORAGE_BUCKET=auditflow-artifacts
```

## Local Run

```powershell
cd "C:\Users\alexh\Documents\Codex\2026-05-28\you-are-my-autonomous-cto-and"
python -m pip install -r requirements.txt
python tools\worker\run_supabase_worker.py --once
```

For a continuously running worker:

```powershell
python tools\worker\run_supabase_worker.py
```

## Pilot Hosting Recommendation

Use a small always-on Python service on Render, Railway, Fly.io, or a comparable container host. Vercel remains the web frontend. Supabase remains durable storage and job state.
