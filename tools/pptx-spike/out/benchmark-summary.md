# PowerPoint Preservation Benchmark Results

## Preservation Matrix

| Approach | Score | Masters | Layouts | Themes | Notes | Tables | Charts | Editable Text Runs |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| python_pptx | 8/8 (1.0) | 1 | 11 | 1 | 3 | 1 | 1 | 23 |
| pptxgenjs | 7/8 (0.875) | 1 | 1 | 1 | 3 | 1 | 1 | 23 |
| hybrid_openxml | 8/8 (1.0) | 1 | 11 | 1 | 3 | 1 | 1 | 23 |

## Timing

- Fixture generation: 31.2 ms
- python-pptx round-trip: 12.49 ms
- pptxgenjs regeneration: 117.18 ms
- Hybrid Open XML clone/edit: 4.43 ms

## Initial Interpretation

- `pptxgenjs` is strong for creating editable new slides, tables, and charts, but it does not parse and preserve an existing prior-year deck as a source template.
- `python-pptx` can inspect slide structure and mutate editable text, but round-tripping can drop or rewrite unsupported package parts such as manually injected notes relationships and is not ideal as the fidelity-preserving core.
- Hybrid Open XML clone/edit preserves the package best because it starts from the original deck and changes only targeted XML nodes. It should be the foundation for template preservation, with a higher-level renderer used for new editable elements when needed.
