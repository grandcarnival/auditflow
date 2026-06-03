# Database Schema

## Tenancy Model

AuditFlow AI uses organization-scoped tenancy. Every project, source file, generated artifact, job, subscription, and audit event belongs to an organization. Access is granted through membership rows and enforced with Postgres Row Level Security.

Authorization data must live in database tables and trusted app metadata, not user-editable metadata.

## Core Tables

```sql
create type public.organization_role as enum ('owner', 'admin', 'member', 'viewer');
create type public.project_status as enum ('draft', 'processing', 'review', 'approved', 'exported', 'archived');
create type public.source_file_type as enum ('pptx_prior_year', 'excel_findings', 'raw_notes', 'pdf', 'other');
create type public.processing_job_status as enum ('queued', 'running', 'needs_review', 'succeeded', 'failed', 'cancelled');
create type public.artifact_type as enum ('extraction_json', 'deck_plan', 'pptx_export', 'preview_image', 'executive_summary', 'chart_data');
create type public.subscription_status as enum ('trialing', 'active', 'past_due', 'canceled', 'unpaid', 'incomplete');

create table public.organizations (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  slug text not null unique,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.organization_memberships (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references public.organizations(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  role public.organization_role not null,
  created_at timestamptz not null default now(),
  unique (organization_id, user_id)
);

create table public.projects (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references public.organizations(id) on delete cascade,
  name text not null,
  fiscal_year integer,
  status public.project_status not null default 'draft',
  created_by uuid references auth.users(id),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.source_files (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references public.organizations(id) on delete cascade,
  project_id uuid not null references public.projects(id) on delete cascade,
  uploaded_by uuid references auth.users(id),
  file_type public.source_file_type not null,
  original_filename text not null,
  storage_bucket text not null,
  storage_path text not null,
  mime_type text not null,
  size_bytes bigint not null,
  sha256 text not null,
  metadata jsonb not null default '{}',
  created_at timestamptz not null default now(),
  unique (organization_id, project_id, sha256)
);

create table public.processing_jobs (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references public.organizations(id) on delete cascade,
  project_id uuid not null references public.projects(id) on delete cascade,
  job_type text not null,
  status public.processing_job_status not null default 'queued',
  input jsonb not null default '{}',
  output jsonb not null default '{}',
  error_message text,
  started_at timestamptz,
  completed_at timestamptz,
  created_at timestamptz not null default now()
);

create table public.extracted_documents (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references public.organizations(id) on delete cascade,
  project_id uuid not null references public.projects(id) on delete cascade,
  source_file_id uuid not null references public.source_files(id) on delete cascade,
  extraction_version text not null,
  content jsonb not null,
  citations jsonb not null default '[]',
  created_at timestamptz not null default now()
);

create table public.deck_templates (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references public.organizations(id) on delete cascade,
  project_id uuid references public.projects(id) on delete set null,
  source_file_id uuid references public.source_files(id) on delete set null,
  name text not null,
  theme jsonb not null default '{}',
  slide_patterns jsonb not null default '[]',
  layout_fingerprint text not null,
  created_at timestamptz not null default now()
);

create table public.generated_artifacts (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references public.organizations(id) on delete cascade,
  project_id uuid not null references public.projects(id) on delete cascade,
  job_id uuid references public.processing_jobs(id) on delete set null,
  artifact_type public.artifact_type not null,
  storage_bucket text,
  storage_path text,
  data jsonb not null default '{}',
  version integer not null default 1,
  created_at timestamptz not null default now()
);

create table public.ai_runs (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references public.organizations(id) on delete cascade,
  project_id uuid references public.projects(id) on delete cascade,
  job_id uuid references public.processing_jobs(id) on delete set null,
  provider text not null default 'openai',
  model text not null,
  workflow_name text not null,
  prompt_version text not null,
  input jsonb not null default '{}',
  output jsonb not null default '{}',
  usage jsonb not null default '{}',
  created_at timestamptz not null default now()
);

create table public.review_comments (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references public.organizations(id) on delete cascade,
  project_id uuid not null references public.projects(id) on delete cascade,
  artifact_id uuid references public.generated_artifacts(id) on delete cascade,
  created_by uuid references auth.users(id),
  body text not null,
  resolved_at timestamptz,
  created_at timestamptz not null default now()
);

create table public.billing_customers (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null unique references public.organizations(id) on delete cascade,
  stripe_customer_id text not null unique,
  created_at timestamptz not null default now()
);

create table public.subscriptions (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references public.organizations(id) on delete cascade,
  stripe_subscription_id text unique,
  status public.subscription_status not null,
  plan_key text not null,
  current_period_end timestamptz,
  entitlements jsonb not null default '{}',
  updated_at timestamptz not null default now()
);

create table public.usage_events (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references public.organizations(id) on delete cascade,
  project_id uuid references public.projects(id) on delete set null,
  event_type text not null,
  quantity numeric not null default 1,
  metadata jsonb not null default '{}',
  created_at timestamptz not null default now()
);

create table public.audit_events (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid references public.organizations(id) on delete set null,
  actor_user_id uuid references auth.users(id) on delete set null,
  action text not null,
  subject_type text not null,
  subject_id uuid,
  metadata jsonb not null default '{}',
  created_at timestamptz not null default now()
);
```

## RLS Policy Direction

Every exposed table must have RLS enabled. Policy implementation should follow these rules:

- Organization members can read organization-scoped rows.
- Owners and admins can manage organization settings, members, billing, and destructive project actions.
- Members can create and edit projects and artifacts depending on entitlement.
- Viewers can read but not mutate.
- Service role access is only used in trusted backend functions and never exposed to the browser.
- Storage access is scoped by organization and project path.

Supabase guidance confirms that Storage access control is enforced through RLS policies on `storage.objects`, and that SSR auth should use `@supabase/ssr` with server-side `getUser()` validation.

Sources:

- Supabase Next.js SSR/Auth docs: https://supabase.com/docs/guides/auth/server-side/nextjs
- Supabase Storage access control: https://supabase.com/docs/guides/storage/security/access-control
- Supabase Edge Function auth context: https://supabase.com/docs/guides/functions/auth-legacy-jwt

