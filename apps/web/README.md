# AuditFlow AI Web App

This directory contains the first lightweight Next.js MVP scaffold.

Implemented:

- Next.js 15 latest patched line
- TypeScript
- Minimal upload UI
- Processing status
- Preservation report display
- Editable PPTX download route

The app calls `tools/workflow/run_mvp_workflow.py`, which runs the current Python preservation workflow.

Blocked locally:

- `npm` / `pnpm` are not available in this shell, so dependencies cannot be installed and the app cannot be run yet.

Planned next:

- Add Tailwind and shadcn/ui once package manager access is available.
- Replace local `.runtime` storage with durable project storage after the end-to-end workflow is proven.
