# Coding Standards And Repository Structure

## Repository Structure

```text
apps/
  web/                         Next.js application
packages/
  ai/                          AI workflows, prompts, schemas
  config/                      Shared lint, TypeScript, env config
  db/                          Typed database helpers and generated types
  documents/                   PDF, Excel, notes extraction
  observability/               Sentry, Mixpanel, logging helpers
  pptx/                        Template analysis and PowerPoint generation
supabase/
  migrations/                  Database migrations
  functions/                   Supabase Edge Functions
docs/
  architecture/                System design
  operations/                  Deployment and runbooks
  roadmap/                     Execution plan
  security/                    Security design
.github/
  workflows/                   CI/CD
```

## Coding Standards

- TypeScript strict mode.
- Zod or JSON Schema for all external and AI-generated data boundaries.
- Server-only clients initialized lazily.
- No service keys in browser bundles.
- No authorization decisions from user-editable metadata.
- Prefer Server Components for data reads.
- Keep Client Components small and interaction-focused.
- Use shadcn/ui primitives before custom controls.
- Use explicit RBAC checks in server mutations.
- Keep AI prompts versioned and tested with fixtures.
- Store generated artifacts and AI outputs with enough metadata to reproduce.

## Naming

- Database tables: plural snake_case.
- TypeScript files: kebab-case except React components may be PascalCase where local convention requires.
- React components: PascalCase.
- Server actions: verb-first names.
- AI workflows: stable snake_case workflow names.

## Pull Request Quality Bar

Every production PR should include:

- Clear scope.
- Tests for changed behavior.
- RLS/security consideration when data access changes.
- Sentry-safe error handling.
- Migration notes when schema changes.
- Updated docs for workflow or architecture changes.

