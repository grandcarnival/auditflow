# Regression Suite

Runs the current preservation reliability gates:

1. Python unit tests.
2. Preservation fidelity benchmark suite.
3. Enterprise fixture suite.

Run:

```powershell
& "C:\Users\alexh\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" tools\regression\run_regression_suite.py
```

Outputs:

- `tools/regression/out/regression-results.json`
- `tools/regression/out/regression-summary.md`

