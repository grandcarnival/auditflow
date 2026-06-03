# Deployment, Observability, And CI/CD

## Deployment Infrastructure

- Vercel hosts the Next.js application.
- Supabase hosts Postgres, Auth, Storage, and Edge Functions.
- GitHub hosts source control and CI workflows.
- Stripe handles billing.
- Sentry handles error monitoring.
- Mixpanel handles product analytics.

## Environments

- Local: developer environment with local Supabase where feasible.
- Preview: Vercel preview deployments for branches.
- Staging: persistent staging environment connected to staging Supabase and Stripe test mode.
- Production: production Vercel and Supabase projects with restricted secrets.

## CI/CD Workflows

Required checks:

- Install dependencies.
- Lint.
- Typecheck.
- Unit tests.
- Database migration validation.
- Build.
- Basic security scan.
- Playwright smoke tests once app UI exists.

Deployment flow:

1. Pull request opens.
2. CI checks run.
3. Vercel preview deployment is created.
4. Smoke tests run against preview URL.
5. Merge to main deploys staging or production depending on branch policy.

## Observability

### Sentry

- Frontend runtime errors.
- Server route/action errors.
- Edge Function errors where integration allows.
- Release tracking.
- User and organization context with privacy controls.

### Mixpanel

Track:

- Project created.
- Files uploaded.
- Processing started.
- Processing failed.
- Deck generated.
- Review approved.
- PPTX exported.
- Billing events.

### Database And Job Logs

Postgres stores durable job events and audit events. Processing logs should avoid sensitive extracted text unless explicitly needed for debugging and protected by retention controls.

## Runbooks

Initial runbooks:

- Failed processing job.
- Broken PowerPoint export.
- Stripe webhook replay.
- Supabase auth incident.
- RLS policy regression.
- OpenAI rate-limit or outage.
- Vercel deployment rollback.

