import { readFile } from "fs/promises";
import path from "path";
import { NextResponse } from "next/server";

export const runtime = "nodejs";
export const maxDuration = 60;

export async function GET(request: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  if (!/^[a-f0-9-]{36}$/.test(id)) {
    return NextResponse.json({ error: "Invalid export id." }, { status: 400 });
  }

  if (process.env.AUDITFLOW_PROCESSOR_MODE === "supabase") {
    return getSupabaseArtifact(id, new URL(request.url).searchParams.get("artifact") ?? "deck");
  }

  const repoRoot = process.env.AUDITFLOW_REPO_ROOT ?? path.resolve(process.cwd(), "..", "..");
  const exportPath = path.join(repoRoot, ".runtime", "jobs", id, "auditflow-export.pptx");
  try {
    const file = await readFile(exportPath);
    return new Response(file, {
      headers: {
        "Content-Type": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "Content-Disposition": 'attachment; filename="auditflow-export.pptx"',
      },
    });
  } catch {
    return NextResponse.json({ error: "Export not found." }, { status: 404 });
  }
}

async function getSupabaseArtifact(jobId: string, artifact: string) {
  const field = artifact === "report" ? "report_path" : artifact === "manifest" ? "manifest_path" : "output_deck_path";
  const response = await supabaseFetch(`/rest/v1/auditflow_jobs?id=eq.${encodeURIComponent(jobId)}&select=${field}`);
  const rows = (await response.json()) as Array<Record<string, string | null>>;
  const objectPath = rows[0]?.[field];
  if (!objectPath) {
    return NextResponse.json({ error: "Artifact not found." }, { status: 404 });
  }

  const bucket = process.env.AUDITFLOW_STORAGE_BUCKET ?? "auditflow-artifacts";
  const file = await supabaseFetch(`/storage/v1/object/${bucket}/${objectPath}`);
  const body = Buffer.from(await file.arrayBuffer());
  const isJson = artifact === "report" || artifact === "manifest";
  return new Response(body, {
    headers: {
      "Content-Type": isJson ? "application/json" : "application/vnd.openxmlformats-officedocument.presentationml.presentation",
      "Content-Disposition": `attachment; filename="${artifact === "deck" ? "auditflow-export.pptx" : `${artifact}.json`}"`,
    },
  });
}

async function supabaseFetch(pathname: string) {
  const url = process.env.SUPABASE_URL;
  const key = process.env.SUPABASE_SERVICE_ROLE_KEY;
  if (!url || !key) {
    throw new Error("Supabase download requires SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY.");
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
