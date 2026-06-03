# PowerPoint Preservation Spike

This spike compares three implementation paths for the AuditFlow AI core moat:

1. `pptxgenjs` regeneration.
2. `python-pptx` parse and round-trip.
3. Hybrid Open XML clone/edit.

The benchmark measures whether each approach preserves:

- Slide masters and layouts.
- Theme XML.
- Tables.
- Charts.
- Speaker notes.
- Editable text.
- Existing slide structure.

## Run

Use the bundled runtime paths:

```powershell
& "C:\Users\alexh\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" tools\pptx-spike\scripts\run_spike.py
```

The script writes generated PPTX files and benchmark JSON/Markdown results under `tools/pptx-spike/out/`.

To run the mini end-to-end core MVP demo:

```powershell
& "C:\Users\alexh\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" tools\pptx-spike\scripts\run_core_mvp_demo.py
```

This creates:

- `tools/pptx-spike/out/current_year_findings.xlsx`
- `tools/pptx-spike/out/auditflow_core_mvp_export.pptx`
- `tools/pptx-spike/out/core-mvp-demo-report.json`

## Result

The first benchmark recommends a hybrid architecture:

- Open XML clone/edit as the preservation core.
- `python-pptx` for inspection.
- `pptxgenjs` for fallback generation of new editable objects.

See `docs/architecture/07-pptx-preservation-spike-results.md`.
