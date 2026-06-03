import { NextResponse } from "next/server";

export const runtime = "nodejs";
export const maxDuration = 30;

type JobRow = {
  id: string;
  status: "queued" | "processing" | "completed" | "failed";
  error_message: string | null;
  preservation_score: number | null;
  package_valid: boolean | null;
  findings_count: number | null;
  duplicated_slides: number | null;
  output_deck_path: string | null;
  report_path: string | null;
  manifest_path: string | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
};

export async function GET(_request: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  if (!/^[a-f0-9-]{36}$/.test(id)) {
    return NextResponse.json({ error: "Invalid job id." }, { status: 400 });
  }

  const response = await supabaseFetch(
    `/rest/v1/auditflow_jobs?id=eq.${encodeURIComponent(id)}&select=id,status,error_message,preservation_score,package_valid,findings_count,duplicated_slides,output_deck_path,report_path,manifest_path,created_at,started_at,completed_at`,
  );
  const rows = (await response.json()) as JobRow[];
  const job = rows[0];
  if (!job) {
    return NextResponse.json({ error: "Job not found." }, { status: 404 });
  }

  return NextResponse.json({
    jobId: job.id,
    status: job.status,
    error: job.error_message,
    preservationScore: job.preservation_score,
    packageValid: job.package_valid,
    findingsCount: job.findings_count,
    duplicatedSlides: job.duplicated_slides,
    downloadUrl: job.output_deck_path ? `/api/exports/${job.id}` : null,
    reportUrl: job.report_path ? `/api/exports/${job.id}?artifact=report` : null,
    manifestUrl: job.manifest_path ? `/api/exports/${job.id}?artifact=manifest` : null,
    createdAt: job.created_at,
    startedAt: job.started_at,
    completedAt: job.completed_at,
  });
}

async function supabaseFetch(pathname: string) {
  const url = process.env.SUPABASE_URL;
  const key = process.env.SUPABASE_SERVICE_ROLE_KEY;
  if (!url || !key) {
    throw new Error("Job status requires SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY.");
  }
  const response = await fetch(`${url}${pathname}`, {
    headers: {
      apikey: key,
      Authorization: `Bearer ${key}`,
    },
  });
  if (!response.ok) {
    throw new Error(`Supabase request failed: ${response.status} ${await response.text()}`);
  }
  return response;
}
