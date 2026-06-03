# Exact Execution Order

## Approval Checkpoint

Large-scale implementation starts only after approval of this planning package.

## Step-By-Step Order

1. Confirm product scope and MVP acceptance criteria.
2. Confirm whether to remain on Next.js 15 latest patched line or move to current stable Next.js.
3. Create Git repository and initial planning commit.
4. Run PowerPoint round-trip spike.
5. Run document extraction spike for XLSX, PDF, and PPTX.
6. Finalize implementation libraries based on spike results.
7. Scaffold Next.js app.
8. Initialize shadcn/ui and app shell.
9. Configure Supabase project and local migrations.
10. Implement database schema and RLS.
11. Add Supabase Auth SSR flow.
12. Build organization, membership, and RBAC services.
13. Build project dashboard.
14. Build signed upload and storage path isolation.
15. Build processing job state machine.
16. Implement deterministic extractors.
17. Implement prompt registry and AI run logging.
18. Implement structured findings extraction.
19. Implement retrieval indexing.
20. Implement executive summary and deck plan workflows.
21. Implement PowerPoint template analyzer.
22. Implement layout matching and content binding.
23. Implement editable PPTX renderer.
24. Implement validation and preview workflow.
25. Add review UI and approval flow.
26. Add Stripe billing and entitlements.
27. Add Sentry, Mixpanel, operational dashboards, and runbooks.
28. Add CI/CD, staging deployment, and smoke tests.
29. Build fixture-based regression test suite.
30. Security hardening and production readiness review.

## First Implementation Sprint After Approval

The first sprint should not start with UI polish. It should de-risk the core value proposition:

1. PowerPoint preservation spike.
2. Extraction spike.
3. Minimal authenticated app shell.
4. Schema and RLS baseline.
5. Upload and processing job skeleton.

