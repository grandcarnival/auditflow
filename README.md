# AuditFlow AI

AuditFlow AI is planned as a production-grade enterprise SaaS platform for converting prior-year audit committee materials, current-year findings, notes, PDFs, and spreadsheet evidence into editable, standardized audit committee PowerPoint decks.

This repository is currently in the approval planning stage. The documents under `docs/` define the architecture, execution roadmap, data model, risk register, and implementation order. Production implementation should begin only after approval of this plan.

## Current Status

- Architecture plan: drafted
- Repository structure: drafted
- Database schema: drafted
- Execution roadmap: drafted
- Technical risks: drafted
- Product requirements analysis: drafted
- Backend service map: drafted
- Billing architecture: drafted
- PowerPoint preservation spike: completed
- Core PPTX preservation package: started
- Excel findings ingestion: started
- MVP content mapping: started
- Table/chart/slide duplication preservation: started and tested
- Core MVP export demo: passing with preservation score 1.0
- Preservation fidelity benchmark suite: passing with suite score 1.0
- Workflow service: started and tested
- Operation manifests: implemented
- Enterprise fixture framework: implemented
- Regression suite: passing
- Real-world readiness report: drafted
- Production web app: manually scaffolded, blocked on package manager availability

## Approval Gate

Before large-scale implementation begins, approve or revise:

1. System architecture
2. Data model and tenancy model
3. PowerPoint preservation strategy
4. AI workflow boundaries
5. Billing and RBAC model
6. Deployment and observability baseline
7. Exact execution order
