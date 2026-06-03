create table if not exists public.auditflow_jobs (
  id uuid primary key,
  status text not null check (status in ('queued', 'processing', 'completed', 'failed')),
  prior_deck_path text not null,
  findings_workbook_path text not null,
  notes_path text,
  output_deck_path text,
  report_path text,
  manifest_path text,
  error_message text,
  preservation_score numeric,
  package_valid boolean,
  findings_count integer,
  duplicated_slides integer,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  started_at timestamptz,
  completed_at timestamptz
);

alter table public.auditflow_jobs enable row level security;

create index if not exists auditflow_jobs_status_created_at_idx
  on public.auditflow_jobs (status, created_at);

insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values (
  'auditflow-artifacts',
  'auditflow-artifacts',
  false,
  52428800,
  array[
    'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/json',
    'text/plain'
  ]
)
on conflict (id) do update
set
  public = excluded.public,
  file_size_limit = excluded.file_size_limit,
  allowed_mime_types = excluded.allowed_mime_types;
